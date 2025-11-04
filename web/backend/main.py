from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import aiohttp
from remixtree import build_tree_async
from remixtree.node import RemixNodes

app = FastAPI(title="Scratch RemixTree API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Scratch RemixTree API",
        "endpoints": {
            "/build/{project_id}": "Stream tree building progress (SSE)",
            "/tree/{project_id}": "Get complete tree as JSON"
        }
    }

@app.get("/build/{project_id}")
async def build_tree_stream(project_id: int, max_depth: int = None):
    """
    stream tree building progress using SSE
    """
    async def event_generator():
        try:
            # create a queue for progress updates
            queue = asyncio.Queue()
            node_count = 0
            
            # send start message
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting tree build...'})}\n\n"
            
            # progress callback that puts updates in the queue
            async def progress_callback(node, depth, status):
                nonlocal node_count
                node_count += 1
                
                event_data = {
                    'type': 'progress',
                    'node': {
                        'id': node.project_id,
                        'title': node.title,
                        'depth': depth,
                        'children_count': len(node.children),
                        'status': status
                    },
                    'total_nodes': node_count
                }
                await queue.put(event_data)
            
            # start building the tree in a background task
            async def build_task():
                try:
                    tree = await build_tree_async(
                        project_id, 
                        max_depth=max_depth,
                        progress_callback=progress_callback
                    )
                    # signal completion with the tree
                    await queue.put(('complete', tree, node_count))
                except Exception as e:
                    # signal error
                    await queue.put(('error', str(e)))
            
            # start the build task
            task = asyncio.create_task(build_task())
            
            # stream updates from the queue
            while True:
                try:
                    # wait for updates with a timeout to keep connection alive
                    update = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # check if it's a completion or error signal
                    if isinstance(update, tuple):
                        if update[0] == 'complete':
                            _, tree, total = update
                            
                            # convert tree to dict
                            def tree_to_dict(node: RemixNodes):
                                return {
                                    'id': node.project_id,
                                    'title': node.title,
                                    'children': [tree_to_dict(child) for child in node.children]
                                }
                            
                            tree_dict = tree_to_dict(tree)
                            
                            completion_data = {
                                'type': 'complete',
                                'message': 'Tree building complete!',
                                'total_nodes': total,
                                'tree': tree_dict
                            }
                            yield f"data: {json.dumps(completion_data)}\n\n"
                            break
                        
                        elif update[0] == 'error':
                            error_data = {
                                'type': 'error',
                                'message': update[1]
                            }
                            yield f"data: {json.dumps(error_data)}\n\n"
                            break
                    else:
                        # normal progress update
                        yield f"data: {json.dumps(update)}\n\n"
                
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield ": keepalive\n\n"
                    continue
            
            # wait for it to complete
            await task
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # no buffer from nginx
        }
    )

@app.get("/tree/{project_id}")
async def get_tree(project_id: int, max_depth: int = None):
    """
    get complete tree as JSON (no streaming) :sob:
    """
    try:
        tree = await build_tree_async(project_id, max_depth=max_depth)
        
        def tree_to_dict(node: RemixNodes):
            return {
                'id': node.project_id,
                'title': node.title,
                'children': [tree_to_dict(child) for child in node.children]
            }
        
        def count_nodes(node):
            return 1 + sum(count_nodes(child) for child in node.children)
        
        return {
            'project_id': project_id,
            'total_nodes': count_nodes(tree),
            'tree': tree_to_dict(tree)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

# for vercel
app = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)