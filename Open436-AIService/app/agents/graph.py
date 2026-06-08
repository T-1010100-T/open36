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


async def crawl_node(state: AgentState) -> AgentState:
    """数据收集节点：Router 调用爬虫工具收集数据"""
    from app.tools.crawler_tools import crawl_search, crawl_webpage

    user_msg = state['user_message']
    intent = state['intent']
    crawled = []
    tool_calls_log = []

    try:
        # 用 LLM 判断需要搜索什么关键词
        plan_prompt = f"""用户请求: {user_msg}
意图: {intent}

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
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            plan = json.loads(match.group()) if match else {'queries': []}

        queries = plan.get('queries', [])
        max_results = plan.get('max_results', 5)

        # 对每个关键词调用爬虫搜索
        for query in queries[:3]:  # 最多3个关键词
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


async def run_agent(user_message: str, user_id: int) -> dict:
    """
    执行Agent工作流 - Router 总指挥架构

    流程：
    1. Router 意图识别
    2. 如果需要数据 → 调用爬虫收集
    3. 分发给下游 Agent 处理
    4. 汇总结果返回
    """
    state: AgentState = {
        'user_message': user_message,
        'user_id': user_id,
        'intent': '',
        'agent_name': '',
        'reply': '',
        'crawled_data': [],
        'tool_calls': [],
        'token_usage': {'input': 0, 'output': 0},
    }

    # Step 1: Router 意图识别
    state = await route_and_plan(state)
    intent = state['intent']

    # Step 2: 根据意图决定是否需要爬取数据
    need_crawl = intent in ('forum', 'problem')

    if need_crawl:
        # Step 3: 调用爬虫收集数据
        state = await crawl_node(state)

    # Step 4: 分发给下游 Agent 处理
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
