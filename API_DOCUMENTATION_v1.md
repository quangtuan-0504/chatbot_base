# Chatbot Application API Documentation

## Table of Contents
1. [Authentication](#authentication)
2. [Users Management](#users-management)
3. [Groups Management](#groups-management)
4. [Collections Management](#collections-management)
5. [Documents Management](#documents-management)
6. [Chat System](#chat-system)
7. [Data Models](#data-models)
8. [Error Handling](#error-handling)

## Base URL
```
https://your-api-domain.com/api/v1
```

## Authentication

All endpoints except `/auth/register` and `/auth/login` require JWT authentication.

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 1. Register User
**POST** `/auth/register`

```json
Request Body:
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "securePassword123",
  "name": "John Doe"
}

Response:
{
  "code": 200,
  "data": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "john_doe",
    "name": "John Doe",
    "system_role": "user",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Create successful"
}
```

### 2. Login
**POST** `/auth/login`

```json
Request Body (Form Data):
{
  "username": "user@example.com",  // email or username
  "password": "securePassword123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "john_doe",
    "name": "John Doe",
    "system_role": "user"
  }
}
```

### 3. Refresh Token
**POST** `/auth/refresh-token`

```json
Request Body:
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

Response: Same as login response
```

### 4. Logout
**POST** `/auth/logout`
- Requires authentication
- Response: `{"code": 200, "message": "Logout successful"}`

### 5. Reset Password
**PUT** `/auth/reset-password`

```json
Request Body:
{
  "current_password": "oldPassword123",
  "new_password": "newPassword123"
}

Response:
{
  "code": 200,
  "message": "Password updated successfully"
}
```

## Users Management

### 1. Get Profile
**GET** `/users/profile`
- Requires authentication
- Returns current user's profile information

### 2. Update Profile
**PUT** `/users/profile`

```json
Request Body:
{
  "email": "newemail@example.com",
  "name": "New Name"
}

Response:
{
  "code": 200,
  "data": {
    "id": "user_id",
    "email": "newemail@example.com",
    "name": "New Name",
    "system_role": "user"
  },
  "message": "Profile updated successfully"
}
```

### 3. View All Users (Admin Only)
**POST** `/users/admin/view-all-users`

```json
Request Body:
{
  "name_filter": "John",
  "email_filter": "@example.com",
  "page": 1,
  "limit": 10
}

Response:
{
  "code": 200,
  "data": [
    {
      "id": "user_id",
      "email": "user@example.com",
      "name": "John Doe",
      "system_role": "user"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10,
  "message": "Users retrieved successfully"
}
```

### 4. Grant Role (Admin Only)
**POST** `/users/admin/grant-role`

```json
Request Body:
{
  "user_id": "user_id_to_update",
  "system_role": "admin"  // "admin", "creator", "user"
}
```

## Groups Management

### 1. Create Group
**POST** `/groups/create-group`
- Requires creator or admin role

```json
Request Body:
{
  "group_name": "My Team",
  "description": "Team for project collaboration",
  "is_public": true,
  "is_hidden": false
}

Response:
{
  "code": 200,
  "data": {
    "id": "group_id",
    "group_name": "My Team",
    "description": "Team for project collaboration",
    "manager_id": "user_id",
    "is_public": true,
    "is_hidden": false,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Group created successfully"
}
```

### 2. Modify Group
**POST** `/groups/modify-group`

```json
Request Body:
{
  "group_id": "group_id",
  "group_name": "Updated Team Name",
  "description": "Updated description",
  "is_public": false,
  "is_hidden": true
}
```

### 3. Get Groups You Created
**POST** `/groups/get-list-group-you-created`
- No request body required
- Returns list of groups created by current user

### 4. Get Groups Shared With You
**POST** `/groups/get-list-group-shared-you`
- No request body required
- Returns list of groups where you are a member

### 5. Get Community Groups
**POST** `/groups/get-list-group-community`
- Returns public groups that are not hidden

### 6. View All Groups (Admin Only)
**POST** `/groups/view-all-groups`

```json
Request Body:
{
  "group_name_filter": "Team",
  "num_member_filter": 5,
  "page": 1,
  "limit": 10
}
```

### 7. Add Member to Group
**POST** `/groups/add-member`

```json
Request Body:
{
  "group_id": "group_id",
  "email": "member@example.com"
}
```

### 8. Remove Member from Group
**POST** `/groups/remove-member`

```json
Request Body:
{
  "group_id": "group_id",
  "email": "member@example.com"
}
```

### 9. View Users in Group
**POST** `/groups/view-users-in-group`

```json
Request Body:
{
  "group_id": "group_id"
}
```

### 10. Remove Group
**POST** `/groups/remove-group`

```json
Request Body:
{
  "group_id": "group_id"
}
```

## Collections Management

### 1. Create Collection
**POST** `/collections/new-collection`
- Requires creator or admin role

```json
Request Body:
{
  "collection_name": "My Documents",
  "description": "Collection for important documents",
  "tags": ["important", "work"],
  "is_public": false,
  "is_hidden": false,
  "status": "active"
}

Response:
{
  "code": 200,
  "data": {
    "id": "collection_id",
    "collection_name": "My Documents",
    "description": "Collection for important documents",
    "tags": ["important", "work"],
    "owner_id": "user_id",
    "is_public": false,
    "is_hidden": false,
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Create successful"
}
```

### 2. Modify Collection
**POST** `/collections/modify-collection`

```json
Request Body:
{
  "collection_id": "collection_id",
  "collection_name": "Updated Collection Name",
  "is_public": true,
  "is_hidden": false
}
```

### 3. Get Collections You Created
**POST** `/collections/get-list-collection-you-created`
- No request body required

### 4. Get Collections Shared With You
**POST** `/collections/get-list-collection-shared-you`
- No request body required

### 5. Get Community Collections
**POST** `/collections/get-list-collection-community`

```json
Request Body:
{
  "search_name": "search_term"
}
```

### 6. View All Collections (Admin Only)
**POST** `/collections/view-all-collections`

```json
Request Body:
{
  "collection_name": "search_term",
  "status": "active",
  "created_after": "2024-01-01T00:00:00Z",
  "created_before": "2024-12-31T23:59:59Z"
}
```

### 7. Share Collection with User
**POST** `/collections/share`

```json
Request Body:
{
  "collection_id": "collection_id",
  "user_email": "user@example.com",
  "role": "viewer"  // "viewer", "editor"
}
```

### 8. Share Collection with Group
**POST** `/collections/shares`

```json
Request Body:
{
  "collection_id": "collection_id",
  "group_id": "group_id",
  "role": "viewer"  // "viewer", "editor"
}
```

### 9. Delete Collection
**POST** `/collections/delete-collection`

```json
Request Body:
{
  "collection_id": "collection_id"
}
```

## Documents Management

### 1. Add Document
**POST** `/documents/add-document`
- Content-Type: `multipart/form-data`

```
Form Data:
- file: (file upload)
- collection_id: "collection_id"
- description: "Document description" (optional)
- file_type: "pdf" (optional)
- file_name: "Custom filename" (optional)

Response:
{
  "code": 200,
  "data": {
    "id": "file_id",
    "original_file_name": "document.pdf",
    "minio_stored_file_name": "document_uuid.pdf",
    "file_path": "collection_id/document_uuid.pdf",
    "file_type": "pdf",
    "description": "Document description",
    "user_id": "user_id",
    "collection_id": "collection_id",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Update successful"
}
```

### 2. Get Documents in Collection
**POST** `/documents/get-list-docs-collection`

```json
Request Body:
{
  "collection_id": "collection_id"
}

Response:
{
  "code": 200,
  "data": [
    {
      "id": "file_id",
      "original_file_name": "document.pdf",
      "file_type": "pdf",
      "description": "Document description",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### 3. Delete Document
**POST** `/documents/delete-file`

```json
Request Body:
{
  "file_id": "file_id",
  "collection_id": "collection_id"
}
```

### 4. Download Document
**POST** `/documents/download-file`
- Content-Type: `multipart/form-data`

```
Form Data:
- collection_id: "collection_id"
- file_id: "file_id"

Response: File stream with appropriate headers
```

## Chat System

### 1. Get Chat List
**GET** `/chats/list-chats`

```json
Response:
{
  "data": [
    {
      "id": "chat_id",
      "title": "Chat about AI",
      "create_at": "2024-01-01T00:00:00Z",
      "update_at": "2024-01-01T01:00:00Z"
    }
  ],
  "total": 1
}
```

### 2. Get Chat History
**POST** `/chats/chat-history/{chatId}`

```json
Response:
{
  "data": {
    "chat_id": "chat_id",
    "history": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      },
      {
        "role": "assistant",
        "content": {
          "answer": "I'm doing well, thank you!",
          "source": []
        }
      }
    ]
  },
  "total": 2
}
```

### 3. Delete Chat
**POST** `/chats/delete-chat/{chatId}`

```json
Response:
{
  "code": 200,
  "message": "Success"
}
```

### 4. Rename Chat
**PUT** `/chats/rename-chat`

```json
Request Body:
{
  "chat_id": "chat_id",
  "new_title": "New Chat Title"
}
```

### 5. Stream Chat (WebSocket)
**WebSocket** `/chats/chat-stream`

```json
Send Message:
{
  "question": "What is artificial intelligence?",
  "modelName": "gpt-4",
  "chatId": "existing_chat_id",  // optional
  "fileIds": ["file_id1", "file_id2"],  // optional
  "collectionId": "collection_id"  // optional
}

Receive Messages:
// Answer chunks
{"type": "answer_chunk", "data": "AI is..."}

// Sources
{"type": "source", "data": [{"title": "Document", "content": "..."}]}

// End of response
{"type": "end_chunk", "data": "[END]"}

// Chat ID (for new chats)
{"type": "chatId", "data": "new_chat_id"}

// Errors
{"type": "error", "data": "Error message"}
```

## Data Models

### User Roles
- `user`: Regular user
- `creator`: Can create collections and groups
- `admin`: Full system access

### Collection Roles
- `owner`: Full control over collection
- `editor`: Can add/remove documents
- `viewer`: Read-only access

### Response Status Codes
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Error Handling

All error responses follow this format:

```json
{
  "code": 400,
  "message": "Error description"
}
```

### Common Error Messages
- `"Missing field: {field_name}"`
- `"Missing parameter: {param_name}"`
- `"Collection not found"`
- `"Chat not found"`
- `"Access denied"`
- `"User not found"`
- `"Invalid credentials"`

## Frontend Implementation Notes

### Authentication Flow
1. User logs in → receive access_token and refresh_token
2. Store tokens securely (localStorage/sessionStorage)
3. Include access_token in all API requests
4. Implement token refresh logic for expired tokens
5. Handle logout by clearing stored tokens

### File Upload
- Use FormData for file uploads
- Show upload progress using XMLHttpRequest progress events
- Handle large file uploads with chunking if needed

### WebSocket Chat
- Establish WebSocket connection with authentication
- Handle real-time message streaming
- Implement reconnection logic for dropped connections
- Display typing indicators and message status

### Permissions
- Check user roles before showing UI elements
- Implement role-based route guards
- Show/hide features based on collection permissions
- Handle permission errors gracefully

### UI Components Needed
1. **Auth Components**: Login, Register, Profile forms
2. **Navigation**: Role-based menu system
3. **Collections**: List, create, share, manage documents
4. **Groups**: Create, manage members, permissions
5. **Chat Interface**: Message list, input, file attachments
6. **Admin Panel**: User management, system overview
7. **File Management**: Upload, download, delete documents
