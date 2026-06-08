"""
爬虫工具 - 调用 CrawlerService API 收集数据
Router Agent 通过这些工具获取原始数据，再分发给下游 Agent 处理
"""
import logging
from langchain_core.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

CRAWLER_URL = settings.CRAWLER_SERVICE_URL


@tool
async def crawl_webpage(url: str) -> dict:
    """
    爬取单个网页，返回 Markdown 内容、标题、元数据。
    适用于需要获取指定网页的完整内容。

    Args:
        url: 要爬取的网页 URL
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{CRAWLER_URL}/crawl/single',
                json={'url': url},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                'success': data.get('success', False),
                'url': data.get('url', ''),
                'title': data.get('title', ''),
                'markdown': data.get('markdown', ''),
                'word_count': data.get('word_count', 0),
            }
    except Exception as e:
        logger.error(f'爬取网页失败 {url}: {e}')
        return {'success': False, 'error': str(e)}


@tool
async def crawl_search(keyword: str, max_results: int = 5, engine: str = 'sogou') -> dict:
    """
    搜索关键词并爬取搜索结果页面。返回多个页面的标题、URL、Markdown 内容。
    适用于需要搜索某个主题的相关资料。

    Args:
        keyword: 搜索关键词
        max_results: 最大结果数，默认5，最大20
        engine: 搜索引擎，可选 sogou/bing/baidu/google，默认 sogou
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{CRAWLER_URL}/crawl/search',
                json={
                    'keyword': keyword,
                    'max_results': min(max_results, 20),
                    'engine': engine,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

            pages = []
            for p in data.get('pages', []):
                if p.get('success'):
                    pages.append({
                        'url': p.get('url', ''),
                        'title': p.get('title', ''),
                        'markdown': p.get('markdown', ''),
                        'word_count': p.get('word_count', 0),
                    })

            return {
                'success': data.get('success', False),
                'keyword': data.get('keyword', keyword),
                'total_pages': data.get('total_pages', 0),
                'pages': pages,
            }
    except Exception as e:
        logger.error(f'搜索爬取失败 "{keyword}": {e}')
        return {'success': False, 'error': str(e)}


@tool
async def crawl_deep(url: str, max_depth: int = 1, max_pages: int = 5) -> dict:
    """
    深度爬取同域页面。从起始 URL 出发，BFS 遍历同域链接。
    适用于需要爬取某个网站的多个页面（如文档站、教程站）。

    Args:
        url: 起始 URL
        max_depth: 最大爬取深度，默认1，最大3
        max_pages: 最大页面数，默认5，最大20
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{CRAWLER_URL}/crawl/deep',
                json={
                    'url': url,
                    'max_depth': min(max_depth, 3),
                    'max_pages': min(max_pages, 20),
                },
                timeout=180.0,
            )
            resp.raise_for_status()
            data = resp.json()

            pages = []
            for p in data.get('pages', []):
                if p.get('success'):
                    pages.append({
                        'url': p.get('url', ''),
                        'title': p.get('title', ''),
                        'markdown': (p.get('markdown') or '')[:3000],
                        'word_count': p.get('word_count', 0),
                    })

            return {
                'success': data.get('success', False),
                'total_pages': data.get('total_pages', 0),
                'pages': pages,
            }
    except Exception as e:
        logger.error(f'深度爬取失败 {url}: {e}')
        return {'success': False, 'error': str(e)}
