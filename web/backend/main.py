from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import aiohttp
from remixtree import build_tree_async
from remixtree.node import RemixNodes

app = FastAPI(title="Scratch RemixTree API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust in production
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
    Stream tree building progress using Server-Sent Events (SSE)
    """
    async def event_generator():
        try:
            # Create a queue for progress updates
            queue = asyncio.Queue()
            node_count = 0
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting tree build...'})}\n\n"
            
            # Progress callback that puts updates in the queue
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
            
            # Start building the tree in a background task
            async def build_task():
                try:
                    tree = await build_tree_async(
                        project_id, 
                        max_depth=max_depth,
                        progress_callback=progress_callback
                    )
                    # Signal completion with the tree
                    await queue.put(('complete', tree, node_count))
                except Exception as e:
                    # Signal error
                    await queue.put(('error', str(e)))
            
            # Start the build task
            task = asyncio.create_task(build_task())
            
            # Stream updates from the queue
            while True:
                try:
                    # Wait for updates with a timeout to keep connection alive
                    update = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # Check if it's a completion or error signal
                    if isinstance(update, tuple):
                        if update[0] == 'complete':
                            _, tree, total = update
                            
                            # Convert tree to dict
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
                        # Regular progress update
                        yield f"data: {json.dumps(update)}\n\n"
                
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield ": keepalive\n\n"
                    continue
            
            # Wait for the task to complete
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
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@app.get("/tree/{project_id}")
async def get_tree(project_id: int, max_depth: int = None):
    """
    Get complete tree as JSON (no streaming)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)