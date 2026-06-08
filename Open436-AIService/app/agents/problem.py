"""
Problem Agent - 出题Agent（算法题生成）
纯加工模式：接收 Router 传来的爬取数据，生成算法题目并调用 HOJ API 创建
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

PROBLEM_SYSTEM_PROMPT = """你是Open436平台的算法题出题Agent。你的职责是根据参考资料生成高质量的算法题目。

工作规范：
1. 题目描述清晰无歧义
2. 输入输出格式明确
3. 示例输入输出必须正确且可验证
4. 隐藏测试用例≥5组，覆盖边界情况
5. 参考解必须能通过所有测试用例
6. 难度标签与实际难度匹配（0简单/1中等/2困难）

你可以使用以下工具：
- create_problem: 创建题目到 HOJ 平台
- list_problems: 查看已有题目列表"""


# 工具定义（OpenAI function calling 格式）
PROBLEM_TOOLS_DEF = [
    {
        'type': 'function',
        'function': {
            'name': 'create_problem',
            'description': '在HOJ平台创建一道算法题目',
            'parameters': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'description': '题目标题'},
                    'description': {'type': 'string', 'description': '题目描述（HTML格式）'},
                    'input': {'type': 'string', 'description': '输入说明'},
                    'output': {'type': 'string', 'description': '输出说明'},
                    'examples': {'type': 'string', 'description': '示例输入输出（HTML格式）'},
                    'hint': {'type': 'string', 'description': '提示/备注'},
                    'time_limit': {'type': 'integer', 'description': '时间限制(ms)', 'default': 1000},
                    'memory_limit': {'type': 'integer', 'description': '内存限制(MB)', 'default': 256},
                    'difficulty': {'type': 'integer', 'description': '难度: 0简单/1中等/2困难'},
                    'tags': {'type': 'array', 'items': {'type': 'string'}, 'description': '标签列表'},
                    'samples': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'input': {'type': 'string'},
                                'output': {'type': 'string'},
                            },
                        },
                        'description': '测试用例列表（含示例和隐藏用例）',
                    },
                    'solution_code': {'type': 'string', 'description': '参考解代码（C++）'},
                },
                'required': ['title', 'description', 'difficulty', 'samples', 'solution_code'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_problems',
            'description': '查看HOJ平台已有的题目列表',
            'parameters': {
                'type': 'object',
                'properties': {
                    'page': {'type': 'integer', 'description': '页码', 'default': 1},
                    'limit': {'type': 'integer', 'description': '每页数量', 'default': 10},
                },
            },
        },
    },
]


async def _call_hoj_api(method: str, path: str, **kwargs) -> dict:
    """调用 HOJ Admin API"""
    # 获取 HOJ token
    async with httpx.AsyncClient() as client:
        login_resp = await client.post(
            f'{settings.HOJ_API_URL}/api/login',
            json={'username': settings.HOJ_ADMIN_USER, 'password': settings.HOJ_ADMIN_PASS},
            timeout=10.0,
        )
        login_resp.raise_for_status()
        token = login_resp.headers.get('authorization', '')

        resp = await client.request(
            method,
            f'{settings.HOJ_API_URL}{path}',
            headers={'Authorization': token, 'Url-Type': 'admin'},
            timeout=30.0,
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json()


async def _call_llm(messages: list, tools: list = None) -> dict:
    """调用LLM API"""
    base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
    url = f'{base_url}/v1/chat/completions'

    payload = {
        'model': settings.LLM_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 4096,
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


async def _execute_tool(tool_name: str, tool_args: dict) -> str:
    """执行工具调用"""
    try:
        if tool_name == 'create_problem':
            # 构造 HOJ API 请求
            samples = tool_args.get('samples', [])
            examples_html = ''
            for s in samples[:3]:  # 前3个作为示例展示
                examples_html += f"<input>{s['input']}</input><output>{s['output']}</output>"

            problem_data = {
                'problem': {
                    'title': tool_args.get('title', ''),
                    'description': tool_args.get('description', ''),
                    'input': tool_args.get('input', ''),
                    'output': tool_args.get('output', ''),
                    'examples': examples_html,
                    'hint': tool_args.get('hint', ''),
                    'timeLimit': tool_args.get('time_limit', 1000),
                    'memoryLimit': tool_args.get('memory_limit', 256),
                    'difficulty': tool_args.get('difficulty', 0),
                    'type': 0,  # ACM模式
                    'auth': 1,  # 公开
                    'judgeMode': 'default',
                    'codeShare': True,
                    'ioScore': 100,
                },
                'samples': samples,
                'tags': [{'name': t} for t in tool_args.get('tags', [])],
                'isUploadTestCase': False,
                'judgeMode': 'default',
            }

            result = await _call_hoj_api('POST', '/api/admin/problem', json=problem_data)
            return json.dumps(result, ensure_ascii=False)

        elif tool_name == 'list_problems':
            page = tool_args.get('page', 1)
            limit = tool_args.get('limit', 10)
            result = await _call_hoj_api(
                'GET',
                f'/api/admin/problem/get-problem-list?currentPage={page}&limit={limit}',
            )
            return json.dumps(result, ensure_ascii=False)

        else:
            return f'未知工具: {tool_name}'

    except Exception as e:
        logger.error(f'工具执行失败 {tool_name}: {e}')
        return f'工具执行失败: {str(e)}'


# 工具函数映射
PROBLEM_TOOLS_MAP = {
    'create_problem': lambda args: _execute_tool('create_problem', args),
    'list_problems': lambda args: _execute_tool('list_problems', args),
}


async def execute_problem_task_with_data(user_message: str, user_id: int, crawled_data: list[dict]) -> dict:
    """
    执行出题任务（带爬取数据）- 纯加工模式

    Router 已经调用爬虫收集好算法题目数据，Problem Agent 只负责：
    1. 阅读爬取的算法题目和解法
    2. 生成新题（改编、换数据、调难度）
    3. 调用 HOJ API 创建题目

    Args:
        user_message: 用户原始请求
        user_id: 管理员ID
        crawled_data: 爬虫收集的页面数据列表 [{url, title, markdown, word_count}]
    """
    try:
        # 将爬取数据格式化为上下文
        context_parts = []
        for i, page in enumerate(crawled_data[:10], 1):
            title = page.get('title', '无标题')
            url = page.get('url', '')
            content = (page.get('markdown') or '')[:3000]
            context_parts.append(f'--- 参考 {i}: {title} ({url}) ---\n{content}')

        crawled_context = '\n\n'.join(context_parts) if context_parts else '（无参考数据，请根据用户描述直接生成题目）'

        enhanced_prompt = f"""用户请求: {user_message}

以下是爬虫收集的算法题目参考资料（共{len(crawled_data)}篇）：
{crawled_context}

请基于以上参考资料，生成新的算法题目。要求：
1. 不能直接照抄原题，需要改编（换数据、改描述、调难度）
2. 题目描述清晰无歧义
3. 生成至少5组测试用例（含边界情况）
4. 提供 C++ 参考解
5. 调用 create_problem 工具创建题目"""

        messages = [
            {'role': 'system', 'content': PROBLEM_SYSTEM_PROMPT},
            {'role': 'user', 'content': enhanced_prompt},
        ]

        tool_calls_log = []
        token_usage = {'input': 0, 'output': 0}

        for _ in range(10):
            data = await _call_llm(messages, PROBLEM_TOOLS_DEF)
            usage = data.get('usage', {})
            token_usage['input'] += usage.get('prompt_tokens', 0)
            token_usage['output'] += usage.get('completion_tokens', 0)

            choice = data['choices'][0]
            message = choice['message']
            finish_reason = choice.get('finish_reason', '')

            if finish_reason == 'stop' or not message.get('tool_calls'):
                return {
                    'reply': message.get('content', ''),
                    'tool_calls': tool_calls_log,
                    'token_usage': token_usage,
                }

            messages.append(message)

            for tc in message['tool_calls']:
                tool_name = tc['function']['name']
                tool_args_str = tc['function']['arguments']
                tool_id = tc['id']

                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                logger.info(f'Problem Agent调用工具: {tool_name}')

                tool_func = PROBLEM_TOOLS_MAP.get(tool_name)
                if not tool_func:
                    tool_result = f'未知工具: {tool_name}'
                    tool_calls_log.append({'tool_name': tool_name, 'status': 'failed', 'error': tool_result})
                else:
                    try:
                        import time
                        start = time.time()
                        result = await tool_func(tool_args)
                        duration = int((time.time() - start) * 1000)
                        tool_calls_log.append({
                            'tool_name': tool_name,
                            'status': 'success',
                            'duration_ms': duration,
                            'result_summary': str(result)[:200],
                        })
                        tool_result = str(result)
                    except Exception as e:
                        tool_result = f'工具执行失败: {str(e)}'
                        tool_calls_log.append({'tool_name': tool_name, 'status': 'failed', 'error': str(e)})

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_id,
                    'content': tool_result,
                })

        return {
            'reply': '任务执行超过最大轮数，请简化指令后重试。',
            'tool_calls': tool_calls_log,
            'token_usage': token_usage,
        }

    except Exception as e:
        logger.error(f'Problem Agent执行失败: {e}')
        return {
            'reply': f'出题Agent执行异常: {str(e)}',
            'tool_calls': [],
            'token_usage': {'input': 0, 'output': 0},
        }
