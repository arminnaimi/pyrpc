# Basic Example

This example demonstrates a complete PyRPC application with a FastAPI backend and a Python client. We'll create a simple blog API with posts and comments.

## Project Structure

```
blog_api/
├── server/
│   ├── main.py
│   ├── models.py
│   └── database.py
└── client/
    └── main.py
```

## Server Implementation

### models.py

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Input Models
class CreatePostInput(BaseModel):
    title: str
    content: str

class UpdatePostInput(BaseModel):
    id: int
    title: Optional[str] = None
    content: Optional[str] = None

class CreateCommentInput(BaseModel):
    post_id: int
    content: str

class GetPostInput(BaseModel):
    id: int

# Output Models
class CommentOutput(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: datetime

class PostOutput(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    comments: List[CommentOutput]
```

### database.py

```python
from datetime import datetime
from typing import Dict, List
from models import PostOutput, CommentOutput

# Simple in-memory database
class Database:
    def __init__(self):
        self.posts: Dict[int, PostOutput] = {}
        self.comments: Dict[int, List[CommentOutput]] = {}
        self.post_id = 0
        self.comment_id = 0
    
    def create_post(self, title: str, content: str) -> PostOutput:
        self.post_id += 1
        post = PostOutput(
            id=self.post_id,
            title=title,
            content=content,
            created_at=datetime.now(),
            comments=[]
        )
        self.posts[post.id] = post
        self.comments[post.id] = []
        return post
    
    def get_post(self, id: int) -> Optional[PostOutput]:
        return self.posts.get(id)
    
    def update_post(self, id: int, title: Optional[str], content: Optional[str]) -> Optional[PostOutput]:
        if id not in self.posts:
            return None
        post = self.posts[id]
        if title:
            post.title = title
        if content:
            post.content = content
        return post
    
    def add_comment(self, post_id: int, content: str) -> Optional[CommentOutput]:
        if post_id not in self.posts:
            return None
        self.comment_id += 1
        comment = CommentOutput(
            id=self.comment_id,
            post_id=post_id,
            content=content,
            created_at=datetime.now()
        )
        self.comments[post_id].append(comment)
        self.posts[post_id].comments = self.comments[post_id]
        return comment

# Create global database instance
db = Database()
```

### main.py

```python
from fastapi import FastAPI
from pyrpc import PyRPCRouter, PyRPCFastAPI
from models import *
from database import db

# Create router
router = PyRPCRouter()

# Post procedures
@router.query("getPost")
def get_post(input: GetPostInput) -> PostOutput:
    post = db.get_post(input.id)
    if not post:
        raise PyRPCError("NOT_FOUND", f"Post {input.id} not found")
    return post

@router.mutation("createPost")
def create_post(input: CreatePostInput) -> PostOutput:
    return db.create_post(input.title, input.content)

@router.mutation("updatePost")
def update_post(input: UpdatePostInput) -> PostOutput:
    post = db.update_post(input.id, input.title, input.content)
    if not post:
        raise PyRPCError("NOT_FOUND", f"Post {input.id} not found")
    return post

# Comment procedures
@router.mutation("createComment")
def create_comment(input: CreateCommentInput) -> CommentOutput:
    comment = db.add_comment(input.post_id, input.content)
    if not comment:
        raise PyRPCError("NOT_FOUND", f"Post {input.post_id} not found")
    return comment

# Create FastAPI app
app = FastAPI()
trpc = PyRPCFastAPI(router)
trpc.mount(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Client Implementation

### main.py

```python
from pyrpc import PyRPCClient, ClientConfig
from models import *  # Re-use server models

async def main():
    # Create client
    client = PyRPCClient(
        ClientConfig(base_url="http://localhost:8000/trpc")
    )
    
    # Create procedures
    posts = client.caller("posts")
    create_post = posts.procedure("createPost", CreatePostInput, PostOutput, is_mutation=True)
    get_post = posts.procedure("getPost", GetPostInput, PostOutput)
    update_post = posts.procedure("updatePost", UpdatePostInput, PostOutput, is_mutation=True)
    create_comment = posts.procedure("createComment", CreateCommentInput, CommentOutput, is_mutation=True)
    
    try:
        # Create a post
        post = await create_post({
            "title": "Hello PyRPC",
            "content": "This is my first post!"
        })
        print(f"Created post: {post.title}")
        
        # Update the post
        updated = await update_post({
            "id": post.id,
            "content": "Updated content!"
        })
        print(f"Updated post: {updated.content}")
        
        # Add a comment
        comment = await create_comment({
            "post_id": post.id,
            "content": "Great post!"
        })
        print(f"Added comment: {comment.content}")
        
        # Get the post with comments
        post = await get_post({"id": post.id})
        print(f"Post has {len(post.comments)} comments")
        
    except PyRPCClientError as e:
        print(f"Error: {e.code} - {e.message}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Running the Example

1. Install dependencies:
```bash
pip install pyrpc[fastapi] uvicorn
```

2. Start the server:
```bash
python server/main.py
```

3. In another terminal, run the client:
```bash
python client/main.py
```

You should see output like:
```
Created post: Hello PyRPC
Updated post: Updated content!
Added comment: Great post!
Post has 1 comments
```

## Key Features Demonstrated

- Type-safe models with Pydantic
- Query and mutation procedures
- Error handling
- Nested data structures (posts with comments)
- Async/await support
- Full IDE support with autocompletion

## Next Steps

- Add [Authentication](auth.md) to protect endpoints
- Implement proper [Error Handling](error-handling.md)
- Use [Nested Routers](nested-routers.md) for better organization
- Create a [Full Stack Example](full-stack.md) with a web frontend 