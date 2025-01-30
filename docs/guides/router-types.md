# Understanding Queries, Mutations, and Procedures

PyRPC provides three main types of route handlers: queries, mutations, and procedures. This guide explains the differences between them and when to use each one.

## Overview

- **Queries**: Used for reading data (similar to HTTP GET)
- **Mutations**: Used for writing data (similar to HTTP POST/PUT/DELETE)
- **Procedures**: A generic type that can be either read or write operations

## Basic Usage

### Queries

Queries are used for read operations. They're marked with `@router.query()`:

```python
@router.query("getUser")
async def get_user(input: UserInput) -> UserOutput:
    return await db.get_user(input.id)
```

### Mutations

Mutations are used for write operations. They're marked with `@router.mutation()`:

```python
@router.mutation("createUser")
async def create_user(input: CreateUserInput) -> UserOutput:
    return await db.create_user(input)
```

### Procedures

Procedures can be either read or write operations, specified by the `is_mutation` parameter:

```python
@router.procedure("complexOperation", is_mutation=False)  # Read operation
async def complex_read(input: ComplexInput) -> ComplexOutput:
    # Complex read operation
    pass

@router.procedure("updateUser", is_mutation=True)  # Write operation
async def update_user(input: UpdateUserInput) -> UserOutput:
    # Write operation
    pass
```

## When to Use Each Type

### Use Queries When

- Reading data from a database
- Fetching user information
- Listing resources
- Performing search operations
- Any operation that doesn't modify data

Example:

```python
@router.query("searchPosts")
async def search_posts(input: SearchInput) -> List[PostOutput]:
    return await db.search_posts(input.query)
```

### Use Mutations When

- Creating new resources
- Updating existing data
- Deleting records
- Any operation that modifies data

Example:

```python
@router.mutation("updateSettings")
async def update_settings(input: SettingsInput) -> SettingsOutput:
    return await db.update_settings(input)
```

### Use Procedures When

- The operation is complex and doesn't clearly fit as a query or mutation
- You need more control over the operation type
- Performing multi-step operations
- Handling complex business logic

Example:

```python
@router.procedure("generateReport", is_mutation=False)
async def generate_report(input: ReportInput) -> ReportOutput:
    stats = await analytics.gather(input.params)
    formatted = await report_formatter.format(stats)
    return ReportOutput(data=formatted)
```

## Real-World Example

Here's a complete example showing all three types in a blog system:

```python
class BlogRouter(PyRPCRouter):
    # Queries for reading data
    @router.query("getPosts")
    async def get_posts(self, input: ListPostsInput) -> List[PostOutput]:
        return await self.db.get_posts(limit=input.limit)
    
    # Mutations for writing data
    @router.mutation("createPost")
    async def create_post(self, input: CreatePostInput) -> PostOutput:
        return await self.db.create_post(input)
    
    # Complex procedure with multiple steps
    @router.procedure("publishPost", is_mutation=True)
    async def publish_post(self, input: PublishPostInput) -> PublishOutput:
        async with self.db.transaction():
            post = await self.db.publish_post(input.post_id)
            await self.search.index_post(post)
            await self.cache.invalidate(['posts'])
            await self.notifications.notify_subscribers(post)
            return PublishOutput(post=post)
```

## Under the Hood

Internally, both `query()` and `mutation()` are shortcuts for `procedure()`:

```python
def query(self, path: str):
    return self.procedure(path, is_mutation=False)

def mutation(self, path: str):
    return self.procedure(path, is_mutation=True)
```

## Best Practices

1. Use the most specific type that fits your use case:
   - Prefer `query()` for clear read operations
   - Prefer `mutation()` for clear write operations
   - Use `procedure()` for complex operations

2. Name your routes clearly:
   - Queries: `getUser`, `listPosts`, `searchItems`
   - Mutations: `createUser`, `updatePost`, `deleteItem`
   - Procedures: `generateReport`, `syncData`, `processUpload`

3. Keep operations focused:
   - Queries should only read data
   - Mutations should have clear write intentions
   - Procedures should handle complex logic that doesn't fit the other categories

4. Consider using procedures when:
   - You need multiple database operations
   - The operation involves external services
   - There's complex business logic
   - You need transaction management

## Best Practices (continued)

5. Error Handling:
   - Use specific error types for different scenarios
   - Always validate input data
   - Provide clear error messages and codes
   - Handle edge cases explicitly

6. Performance:
   - Implement pagination for large datasets
   - Cache frequently accessed query results
   - Consider chunking large responses
   - Use appropriate database indexes

7. Security:
   - Always validate input data
   - Use middleware for authentication/authorization
   - Implement rate limiting for public endpoints
   - Log security-relevant events

8. Testing:
   - Write unit tests for each route
   - Test error cases explicitly
   - Use integration tests for complex procedures
   - Mock external services in tests

## Error Handling

PyRPC provides robust error handling for all route types. Here's how to handle errors effectively:

```python
from pyrpc.errors import PyRPCError, NotFoundError

class UserRouter(PyRPCRouter):
    @router.query("getUser")
    async def get_user(self, input: UserInput) -> UserOutput:
        try:
            user = await self.db.get_user(input.id)
            if not user:
                raise NotFoundError(f"User {input.id} not found")
            return UserOutput(user=user)
        except DatabaseError as e:
            # Convert database errors to PyRPC errors
            raise PyRPCError("Database error", code="DB_ERROR") from e
        except Exception as e:
            # Log unexpected errors and return a safe error response
            logger.error(f"Unexpected error in getUser: {e}")
            raise PyRPCError("Internal server error", code="INTERNAL_ERROR") from e

    @router.mutation("createUser")
    async def create_user(self, input: CreateUserInput) -> UserOutput:
        try:
            # Validate unique constraints
            if await self.db.user_exists(input.email):
                raise PyRPCError("Email already exists", code="DUPLICATE_EMAIL")
            
            user = await self.db.create_user(input)
            return UserOutput(user=user)
        except ValidationError as e:
            raise PyRPCError(str(e), code="VALIDATION_ERROR") from e

## Type Safety and Validation

PyRPC leverages Python's type system and Pydantic for robust type safety and validation:

```python
from pydantic import BaseModel, EmailStr, Field

# Input models with validation
class CreateUserInput(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    age: int = Field(..., ge=0, le=150)

# Output models
class UserOutput(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime

class UserRouter(PyRPCRouter):
    @router.mutation("createUser")
    async def create_user(self, input: CreateUserInput) -> UserOutput:
        # Input is automatically validated by Pydantic
        user = await self.db.create_user(input.model_dump())
        # Output is automatically serialized
        return UserOutput.model_validate(user)

    @router.query("searchUsers")
    async def search_users(
        self,
        input: SearchUsersInput = Field(default_factory=SearchUsersInput)
    ) -> List[UserOutput]:
        # Default values and optional parameters
        users = await self.db.search_users(
            query=input.query,
            limit=input.limit or 10,
            offset=input.offset or 0
        )
        return [UserOutput.model_validate(user) for user in users]
```

## Middleware and Hooks

PyRPC supports middleware for all route types:

```python
from pyrpc.middleware import Middleware
from typing import Callable, Any

# Authentication middleware
class AuthMiddleware(Middleware):
    async def before_handler(self, ctx: Context, next: Callable) -> Any:
        # Check auth token
        token = ctx.headers.get("authorization")
        if not token:
            raise PyRPCError("Unauthorized", code="UNAUTHORIZED")
        
        # Validate token and set user in context
        user = await validate_token(token)
        ctx.user = user
        
        return await next(ctx)

# Rate limiting middleware
class RateLimitMiddleware(Middleware):
    async def before_handler(self, ctx: Context, next: Callable) -> Any:
        # Check rate limits
        await self.check_rate_limit(ctx)
        return await next(ctx)

# Using middleware in your router
class UserRouter(PyRPCRouter):
    middleware = [AuthMiddleware(), RateLimitMiddleware()]

    @router.query("getProfile")
    async def get_profile(self, input: Empty) -> UserProfile:
        # ctx.user is set by AuthMiddleware
        return await self.db.get_profile(self.ctx.user.id)

    @router.query("getPublicProfile")
    async def get_public_profile(self, input: PublicProfileInput) -> PublicProfile:
        return await self.db.get_public_profile(input.username)
```
