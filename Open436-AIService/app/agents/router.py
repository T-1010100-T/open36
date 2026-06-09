"""
Router Agent - 主路由Agent（意图识别与任务分发）
使用OpenAI兼容API（DeepSeek/Claude等）
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """你是Open436平台的AI助手主路由。你的职责是理解用户的意图，并将其分发给对应的专业Agent处理。

意图分类规则：
1. chat - 日常对话、闲聊、问候、问好、打招呼、通用问题咨询
2. forum - 论坛相关，包括：发帖、编辑帖子、查看帖子、搜索资料后整理发帖、搜集信息并发帖、研究某个主题并发帖
3. problem - 出题相关，包括：创建算法题、生成测试用例、搜索算法题目并改编、从LeetCode/Codeforces找题
4. query - 仅查询（查看板块列表、查看任务状态、查看帖子列表），不涉及创建内容
5. unclear - 无法识别，需要澄清

关键判断：
- 如果用户说"搜索/搜集/爬取/研究 + 某个主题"，隐含意图是收集资料并创建内容，应分类为 forum
- 如果用户说"找题/搜题/出题"，应分类为 problem
- 只有纯粹的"查看/查询/列出"才是 query

请只返回一个JSON对象，格式如下：
{"intent": "chat|forum|problem|query|unclear", "reason": "简短说明分类理由"}"""


async def classify_intent(user_message: str) -> dict:
    """
    使用LLM对用户消息进行意图分类

    Returns:
        {"intent": "forum|problem|query|unclear", "reason": "..."}
    """
    try:
        base_url = settings.LLM_BASE_URL or 'https://api.deepseek.com'
        url = f'{base_url}/v1/chat/completions'

        payload = {
            'model': settings.LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': ROUTER_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_message},
            ],
            'temperature': 0.3,
            'max_tokens': 256,
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

        content = data['choices'][0]['message']['content'].strip()

        # 解析JSON
        if content.startswith('{'):
            result = json.loads(content)
        else:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {'intent': 'unclear', 'reason': '无法解析LLM响应'}

        valid_intents = {'chat', 'forum', 'problem', 'query', 'unclear'}
        if result.get('intent') not in valid_intents:
            result = {'intent': 'unclear', 'reason': '意图分类无效'}

        logger.info(f'意图分类: {result}')
        return result

    except Exception as e:
        logger.error(f'意图分类失败: {e}')
        return {'intent': 'unclear', 'reason': f'分类异常: {str(e)}'}
