import aiohttp
from rich.console import Console

console = Console()

async def fetch_project_data(session, project_id):
    """get basic info for a scratch project"""
    url = f"https://api.scratch.mit.edu/projects/{project_id}"
    try:
        async with session.get(url) as response:
            if response.status == 404:
                console.print(f"[bold red]✗ WHOOPS (404):[/bold red] Couldn't find project {project_id}. Maybe it's gone?")
                return None
            if response.status != 200:
                console.print(f"[bold red]✗ BUMMER:[/bold red] API status {response.status} when trying to fetch data for {project_id}")
                return None
            return await response.json()
    except Exception as e:
        console.print(f"[bold red]✗ CONNECTION FAILED:[/bold red] Error fetching {url}: {e}")
        return None


async def get_root_id(session, project_id):
    """tells me where it all actually came from"""
    data = await fetch_project_data(session, project_id)
    if data and data.get("remix"):
        root_id = data["remix"].get("root")
        return root_id if root_id else project_id
    return project_id


async def fetch_remixes_batch(session, url, project_id, offset, verbose=False):
    """takes a batch of remixes from the scratch api, obvisously"""
    import time
    start_time = time.perf_counter()
    try:
        async with session.get(url) as response:
            end_time = time.perf_counter()
            if verbose:
                elapsed = end_time - start_time
                console.print(f"[dim]  [Batch][/dim] Got a remix chunk for {project_id} (offset {offset}), took {elapsed:.4f}s")
            
            if response.status == 200:
                return await response.json()
            return []
    except Exception as e:
        console.print(f"[bold red]✗ ERROR GETTING BATCH:[/bold red] Failed to fetch chunk for {project_id}: {e}")
        return []


async def get_all_remixes(session, project_id, num_remixes, verbose=False):
    """Sets up all the quick, concurrent tasks to fetch remixes for one project."""
    import asyncio
    from rich.progress import track
    
    if num_remixes == 0:
        return []
    
    tasks = []
    for offset in range(0, num_remixes, 40):
        url = f"https://api.scratch.mit.edu/projects/{project_id}/remixes?limit=40&offset={offset}"
        tasks.append(fetch_remixes_batch(session, url, project_id, offset, verbose))
    
    if len(tasks) > 5 and not verbose:
        results = []
        for future in track(
            asyncio.as_completed(tasks), 
            total=len(tasks), 
            description=f"  [cyan]Grabbing {num_remixes} remixes for {project_id}...",
            console=console
        ):
            batch = await future
            if batch:
                results.append(batch)
    else:
        results = await asyncio.gather(*tasks)
        
    all_remixes = [remix for batch in results if batch for remix in batch]
    return all_remixes