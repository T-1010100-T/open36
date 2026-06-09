"""
多Agent编排 - Router 总指挥架构

Router Agent 负责：
1. 意图识别
2. 判断是否需要爬取数据
3. 调用 Crawler Agent 收集数据
4. 将数据分发给下游 Agent（Forum/Problem）处理
5. 汇总结果返回
"""
import json
import logging
from typing import TypedDict

import httpx

from app.config import settings
from app.agents.router import classify_intent

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Agent状态"""
    user_message: str
    user_id: int
    intent: str
    agent_name: str
    reply: str
    crawled_data: list[dict]  # 爬虫收集的原始数据
    tool_calls: list[dict]
    token_usage: dict


# ============== Router 总指挥 ==============

ROUTER_ORCHESTRATOR_PROMPT = """你是Open436平台的总指挥Router。你有两个职责：
1. 判断用户意图
2. 如果用户需要发帖或出题，先用爬虫工具收集相关数据

可用的爬虫工具：
- crawl_webpage(url): 爬取单个网页
- crawl_search(keyword, max_results, engine): 搜索关键词并爬取结果
- crawl_deep(url, max_depth, max_pages): 深度爬取同域页面

请返回JSON，格式如下：
{
  "intent": "forum|problem|chat|query|unclear",
  "need_crawl": true/false,
  "crawl_queries": ["搜索关键词1", "搜索关键词2"],
  "reason": "简短说明"
}

规则：
- chat/query/unclear 不需要爬取
- forum（发帖）通常需要搜索相关资料
- problem（出题）通常需要搜索算法题目和解法
- 用户明确说"不需要搜索"时 need_crawl=false"""


async def _call_llm(messages: list, tools: list = None) -> dict:
    """调用OpenAI兼容API"""
    base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
    url = f'{base_url}/v1/chat/completions'

    payload = {
        'model': settings.LLM_MODEL,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 1024,
    }
    if tools:
        payload['tools'] = tools

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {settings.ANTHROPIC_API_KEY}'},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()


async def route_and_plan(state: AgentState) -> AgentState:
    """Router：意图识别 + 判断是否需要爬取"""
    result = await classify_intent(state['user_message'])
    state['intent'] = result['intent']
    state['agent_name'] = 'router'
    logger.info(f'意图分类: {result}')
    return state


def _should_crawl(intent: str, user_message: str) -> bool:
    """判断是否需要爬取数据

    规则：
    - chat/query/unclear 不需要
    - 用户消息超过 500 字符，认为已提供内容，不需要爬取
    - 其他 forum/problem 意图需要爬取
    """
    if intent not in ('forum', 'problem'):
        return False
    # 用户已提供大量内容（粘贴文章），跳过爬取
    if len(user_message) > 500:
        logger.info(f'用户消息较长({len(user_message)}字符)，跳过爬取')
        return False
    return True


async def crawl_node(state: AgentState) -> AgentState:
    """数据收集节点：Router 调用爬虫工具收集数据

    智能判断：
    - 用户消息中有 URL → 并行 crawl_webpage 爬取所有页面
    - 没有 URL → 用 LLM 规划关键词，crawl_search 搜索
    """
    import asyncio
    from app.tools.crawler_tools import crawl_search, crawl_webpage
    import re as _re

    user_msg = state['user_message']
    crawled = []
    tool_calls_log = []

    try:
        # 检查用户消息中是否有 URL
        url_pattern = r'https?://[^\s<>"\')\]]+'
        urls = _re.findall(url_pattern, user_msg)

        if urls:
            # 有 URL → 并行爬取（asyncio.gather 并发执行）
            urls = urls[:10]  # 最多10个URL

            async def _crawl_one(url: str) -> dict | None:
                logger.info(f'爬取网页: {url}')
                result = await crawl_webpage.ainvoke({'url': url})
                tool_calls_log.append({
                    'tool_name': 'crawl_webpage',
                    'status': 'success' if result.get('success') else 'failed',
                    'url': url,
                })
                return result if result.get('success') else None

            # 并行执行所有爬取任务
            results = await asyncio.gather(*[_crawl_one(url) for url in urls])
            crawled = [r for r in results if r is not None]
            logger.info(f'并行爬取完成: {len(crawled)}/{len(urls)} 成功')
        else:
            # 没有 URL → 用 LLM 规划搜索关键词
            plan_prompt = f"""用户请求: {user_msg}

请判断需要搜索哪些关键词来收集数据。返回JSON格式：
{{"queries": ["关键词1", "关键词2"], "max_results": 5}}

如果用户已经给了明确的搜索词，直接使用。不需要搜索则返回空列表。"""

            data = await _call_llm([
                {'role': 'system', 'content': '你是数据收集规划师。根据用户请求，规划需要搜索的关键词。只返回JSON。'},
                {'role': 'user', 'content': plan_prompt},
            ])

            content = data['choices'][0]['message']['content'].strip()
            if content.startswith('{'):
                plan = json.loads(content)
            else:
                match = _re.search(r'\{.*\}', content, _re.DOTALL)
                plan = json.loads(match.group()) if match else {'queries': []}

            queries = plan.get('queries', [])
            max_results = plan.get('max_results', 5)

            for query in queries[:3]:
                logger.info(f'爬取搜索: {query}')
                result = await crawl_search.ainvoke({
                    'keyword': query,
                    'max_results': max_results,
                })
                tool_calls_log.append({
                    'tool_name': 'crawl_search',
                    'status': 'success' if result.get('success') else 'failed',
                    'query': query,
                    'pages_count': len(result.get('pages', [])),
                })
                if result.get('success'):
                    crawled.extend(result.get('pages', []))

        state['crawled_data'] = crawled
        state['tool_calls'] = tool_calls_log
        logger.info(f'爬取完成: {len(crawled)} 个页面')

    except Exception as e:
        logger.error(f'数据收集失败: {e}')
        state['crawled_data'] = []
        state['tool_calls'] = [{'tool_name': 'crawl', 'status': 'failed', 'error': str(e)}]

    return state


async def forum_node(state: AgentState) -> AgentState:
    """论坛Agent：纯加工，接收爬取数据生成帖子"""
    from app.agents.forum import execute_forum_task_with_data

    result = await execute_forum_task_with_data(
        user_message=state['user_message'],
        user_id=state['user_id'],
        crawled_data=state.get('crawled_data', []),
    )
    state['agent_name'] = 'forum'
    state['reply'] = result['reply']
    state['tool_calls'].extend(result.get('tool_calls', []))
    state['token_usage'] = result['token_usage']
    return state


async def problem_node(state: AgentState) -> AgentState:
    """出题Agent：纯加工，接收爬取数据生成题目"""
    from app.agents.problem import execute_problem_task_with_data

    result = await execute_problem_task_with_data(
        user_message=state['user_message'],
        user_id=state['user_id'],
        crawled_data=state.get('crawled_data', []),
    )
    state['agent_name'] = 'problem'
    state['reply'] = result['reply']
    state['tool_calls'].extend(result.get('tool_calls', []))
    state['token_usage'] = result['token_usage']
    return state


async def chat_node(state: AgentState) -> AgentState:
    """通用聊天节点：直接对话，不走爬虫"""
    try:
        base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
        url = f'{base_url}/v1/chat/completions'

        CHAT_SYSTEM_PROMPT = """你是Open436平台的AI助手，名叫小46。你性格友好、专业、简洁。
- 可以回答日常问题、闲聊、提供帮助
- 涉及平台操作时，可以引导用户使用具体功能（发帖、出题等）
- 回复简洁自然，不要过度使用markdown格式"""

        payload = {
            'model': settings.LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': CHAT_SYSTEM_PROMPT},
                {'role': 'user', 'content': state['user_message']},
            ],
            'temperature': 0.7,
            'max_tokens': 1024,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json=payload,
                headers={'Authorization': f'Bearer {settings.ANTHROPIC_API_KEY}'},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()

        reply = data['choices'][0]['message']['content'].strip()
        usage = data.get('usage', {})

        state['agent_name'] = 'chat'
        state['reply'] = reply
        state['tool_calls'] = []
        state['token_usage'] = {
            'input': usage.get('prompt_tokens', 0),
            'output': usage.get('completion_tokens', 0),
        }
    except Exception as e:
        logger.error(f'聊天Agent异常: {e}')
        state['agent_name'] = 'chat'
        state['reply'] = f'抱歉，处理消息时出现问题：{str(e)}'
        state['tool_calls'] = []
        state['token_usage'] = {'input': 0, 'output': 0}

    return state


async def query_node(state: AgentState) -> AgentState:
    """查询节点"""
    state['agent_name'] = 'router'
    state['reply'] = f'收到您的查询："{state["user_message"]}"。查询功能正在完善中。'
    state['tool_calls'] = []
    state['token_usage'] = {'input': 0, 'output': 0}
    return state


async def unclear_node(state: AgentState) -> AgentState:
    """澄清节点"""
    state['agent_name'] = 'router'
    state['reply'] = (
        '抱歉，我没有完全理解您的指令。您可以：\n'
        '- 直接描述需求，例如"帮我搜集XXX资料发个帖子"或"生成一道算法题"\n'
        '- 或者直接和我聊天也可以哦'
    )
    state['tool_calls'] = []
    state['token_usage'] = {'input': 0, 'output': 0}
    return state


async def decompose_task(user_message: str) -> list[dict] | None:
    """任务拆解：判断是否需要将一个请求拆分为多个子任务

    场景：用户给一个训练页/题单 URL，要求爬取多道题并分别发帖
    返回：子任务列表 [{"url": "...", "action": "forum|problem", "description": "..."}]
    返回 None 表示不需要拆解
    """
    import re as _re

    # 提取 URL
    url_pattern = r'https?://[^\s<>"\')\]]+'
    urls = _re.findall(url_pattern, user_message)

    if not urls:
        return None

    # 用 LLM 判断是否需要拆解
    decompose_prompt = f"""用户请求: {user_message}

URL: {urls[0]}

判断这个请求是否需要拆分为多个子任务。例如：
- "爬取训练页前5题，每题发一个帖子" → 需要拆解为5个子任务
- "爬取这个页面并发帖" → 不需要拆解，单个任务

如果需要拆解，请返回 JSON 格式：
{{
  "need_decompose": true,
  "tasks": [
    {{"url": "https://...", "action": "forum", "description": "爬取题目并生成帖子"}},
    ...
  ]
}}

如果不需要拆解：
{{"need_decompose": false}}

注意：
- 对于洛谷训练页(luogu.com.cn/training/XXX)，如果用户要求爬取多道题，需要拆解
- 洛谷题目URL格式: https://www.luogu.com.cn/problem/PXXXX
- 只返回 JSON，不要其他内容"""

    try:
        data = await _call_llm([
            {'role': 'system', 'content': '你是任务拆解专家。分析用户请求，判断是否需要拆分为多个子任务。只返回JSON。'},
            {'role': 'user', 'content': decompose_prompt},
        ])

        content = data['choices'][0]['message']['content'].strip()
        # 去掉可能的 markdown 代码块标记
        if '```' in content:
            content = _re.sub(r'```json?\s*', '', content)
            content = content.replace('```', '').strip()

        if content.startswith('{'):
            result = json.loads(content)
        else:
            match = _re.search(r'\{.*\}', content, _re.DOTALL)
            result = json.loads(match.group()) if match else {}

        if result.get('need_decompose') and result.get('tasks'):
            logger.info(f'任务拆解: {len(result["tasks"])} 个子任务')
            return result['tasks']

    except Exception as e:
        logger.error(f'任务拆解失败: {e}')

    return None


async def run_agent(user_message: str, user_id: int) -> dict:
    """
    执行Agent工作流 - Router 总指挥架构

    流程：
    1. Router 意图识别
    2. 判断是否需要任务拆解（多个子任务）
    3. 如果需要拆解 → 并行处理多个子任务
    4. 如果不需要拆解 → 单任务流程
    """
    import asyncio

    # Step 1: Router 意图识别
    intent_result = await classify_intent(user_message)
    intent = intent_result['intent']
    logger.info(f'意图分类: {intent_result}')

    # Step 2: 判断是否需要任务拆解
    sub_tasks = await decompose_task(user_message)

    if sub_tasks and len(sub_tasks) > 1:
        # 多子任务模式：并行爬取，逐个处理
        logger.info(f'多子任务模式: {len(sub_tasks)} 个任务')
        return await _run_multi_tasks(sub_tasks, user_id, intent)

    # 单任务模式
    state: AgentState = {
        'user_message': user_message,
        'user_id': user_id,
        'intent': intent,
        'agent_name': 'router',
        'reply': '',
        'crawled_data': [],
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }

    need_crawl = _should_crawl(intent, user_message)

    if need_crawl:
        state = await crawl_node(state)

    if intent == 'forum':
        state = await forum_node(state)
    elif intent == 'problem':
        state = await problem_node(state)
    elif intent == 'query':
        state = await query_node(state)
    elif intent == 'chat':
        state = await chat_node(state)
    else:
        state = await unclear_node(state)

    return {
        'reply': state['reply'],
        'intent': state['intent'],
        'agent_name': state['agent_name'],
        'tool_calls': state['tool_calls'],
        'token_usage': state['token_usage'],
    }


async def _run_multi_tasks(sub_tasks: list[dict], user_id: int, intent: str) -> dict:
    """处理多个子任务：并行爬取 + 逐个处理"""
    import asyncio
    from app.tools.crawler_tools import crawl_webpage

    # Step 1: 并行爬取所有子任务的 URL
    async def _crawl_task(task: dict) -> dict | None:
        url = task.get('url', '')
        if not url:
            return None
        logger.info(f'子任务爬取: {url}')
        result = await crawl_webpage.ainvoke({'url': url})
        return result if result.get('success') else None

    crawl_results = await asyncio.gather(*[_crawl_task(t) for t in sub_tasks])
    crawled_data = [r for r in crawl_results if r is not None]
    logger.info(f'子任务爬取完成: {len(crawled_data)}/{len(sub_tasks)} 成功')

    # Step 2: 逐个处理每个子任务
    replies = []
    all_tool_calls = []
    total_tokens = {'input': 0, 'output': 0}

    for i, (task, crawled) in enumerate(zip(sub_tasks, crawl_results)):
        if not crawled:
            replies.append(f'❌ 子任务 {i+1}: 爬取失败 - {task.get("url", "")}')
            continue

        task_state: AgentState = {
            'user_message': task.get('description', task.get('url', '')),
            'user_id': user_id,
            'intent': intent,
            'agent_name': 'router',
            'reply': '',
            'crawled_data': [crawled],
            'tool_calls': [],
            'token_usage': {'input': 0, 'output': 0},
        }

        if intent == 'forum' or task.get('action') == 'forum':
            task_state = await forum_node(task_state)
        elif intent == 'problem' or task.get('action') == 'problem':
            task_state = await problem_node(task_state)
        else:
            task_state = await forum_node(task_state)

        replies.append(f'**子任务 {i+1}**: {task.get("description", task.get("url", ""))}\n{task_state["reply"]}')
        all_tool_calls.extend(task_state.get('tool_calls', []))
        total_tokens['input'] += task_state['token_usage'].get('input', 0)
        total_tokens['output'] += task_state['token_usage'].get('output', 0)

    # 汇总结果
    summary = f'✅ 共处理 {len(sub_tasks)} 个子任务，成功 {len(crawled_data)} 个\n\n'
    summary += '\n\n---\n\n'.join(replies)

    return {
        'reply': summary,
        'intent': intent,
        'agent_name': 'router',
        'tool_calls': all_tool_calls,
        'token_usage': total_tokens,
    }
