import sys
import time
import asyncio
import aiohttp
from node import RemixNodes

if len(sys.argv) == 1:
    print("usage: python tree_async.py <PROJECT_ID>")
    sys.exit(1)

PROJECT_ID = sys.argv[1]
total_children_count = 0


async def fetch_project_data(session, project_id):
    url = f"https://api.scratch.mit.edu/projects/{project_id}"
    try:
        async with session.get(url) as response:
            if response.status == 404:
                print("Got 404, perhaps the project you're trying to access is not there?")
                sys.exit(1)
            if response.status != 200:
                print(f"Getting project data failed with status code: {response.status}")
                return None
            return await response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


async def get_root_id(session, project_id):
    data = await fetch_project_data(session, project_id)
    if data and data.get("remix"):
        root_id = data["remix"].get("root")
        return root_id if root_id else project_id
    return project_id


async def get_all_remixes(session, project_id, num_remixes):
    if num_remixes == 0:
        return []
    
    tasks = []
    for offset in range(0, num_remixes, 40):
        url = f"https://api.scratch.mit.edu/projects/{project_id}/remixes?limit=40&offset={offset}"
        tasks.append(fetch_remixes_batch(session, url, project_id, offset))
    
    # i dont understand what im doing lol
    results = await asyncio.gather(*tasks)
    
    all_remixes = []
    for batch in results:
        if batch:
            all_remixes.extend(batch)
    
    return all_remixes


async def fetch_remixes_batch(session, url, project_id, offset):
    try:
        start_time = time.perf_counter()
        async with session.get(url) as response:
            end_time = time.perf_counter()
            print(f"getting remixes for {project_id} (offset {offset}), took {(end_time - start_time):.4f} seconds")
            if response.status == 200:
                return await response.json()
            return []
    except Exception as e:
        print(f"rrror fetching remixes batch {url}: {e}")
        return []


async def build_remix_tree(session, project_id, max_depth=None, current_depth=0):
    """RECURSIVELY make da tree"""
    global total_children_count
    
    node = RemixNodes(project_id)
    
    if max_depth is not None and current_depth >= max_depth:
        return node
    
    data = await fetch_project_data(session, project_id)
    if not data:
        return node
    
    num_remixes = data.get("stats", {}).get("remixes", 0)
    
    if num_remixes > 0:
        remixes = await get_all_remixes(session, project_id, num_remixes)
        
        child_tasks = []
        for remix in remixes:
            remix_id = remix["id"]
            total_children_count += 1
            child_tasks.append(
                build_remix_tree(session, remix_id, max_depth, current_depth + 1)
            )
        
        # wait for teh kids
        children = await asyncio.gather(*child_tasks)
        
        # add all the kids
        for child in children:
            node.add_child(child)
    
    return node


async def main():
    global total_children_count
    
    timeout = aiohttp.ClientTimeout(total=300) # timout after 300 secs
    connector = aiohttp.TCPConnector(limit=50)  # max 50 connections at once
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # get root
        root = await get_root_id(session, PROJECT_ID)
        
        # get root remix count
        root_data = await fetch_project_data(session, root)
        if not root_data:
            print("Failed to fetch root project data")
            sys.exit(1)
        
        root_remix_count = root_data.get("stats", {}).get("remixes", 0)
        
        if root_remix_count > 5000:
            print("bro is tryna kill the scratch servers (joke) it'll take forever tho")
            # sys.exit(0)
            # >:D
        
        print(f"the project initially came from {root}")
        print(f"that 'root' has {root_remix_count} DIRECT remixes")
        print(f"making tree from {root}...")
        
        # maek da tree
        start_time = time.perf_counter()
        tree = await build_remix_tree(session, root)
        end_time = time.perf_counter()
        
        elapsed_time = end_time - start_time
        print(f"\ndone hehe, in total we have {total_children_count} projects :O")
        tree.print_tree()
        print(f"\nbuilding the tree took {elapsed_time:.4f} seconds.")

# i put this cuz im a good boyyy
if __name__ == "__main__":
    asyncio.run(main())