
from .tree_builder import build_remix_tree
from .node import RemixNodes
from .api import get_root_id, fetch_project_data
import aiohttp
import asyncio

async def build_tree_async(project_id, max_depth=None, timeout=300):
    """async function to get tree without CLI integration"""
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        root = await get_root_id(session, project_id)
        tree = await build_remix_tree(session, root, "root", max_depth, progress=None, verbose=False)
        return tree

def build_tree(project_id, max_depth=None):
    """sync wrapper"""
    return asyncio.run(build_tree_async(project_id, max_depth))

__all__ = ['build_tree', 'build_tree_async', 'RemixNodes']