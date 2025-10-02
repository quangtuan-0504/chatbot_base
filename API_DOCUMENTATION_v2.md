# Chatbot API Documentation

## Overview
This document provides comprehensive API documentation for the Chatbot application. The API follows REST principles and uses JWT tokens for authentication.

**Base URL:** `http://localhost:8000` (adjust according to your deployment)

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Response Format
All responses follow this standard format:
```json
{
  "code": 200,
  "message": "Success",
  "data": { ... }
}
```

## User Roles
- **admin**: Full system access
- **creator**: Can create collections and groups
- **user**: Basic user access

---

## 1. Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "johndoe", // optional
  "name": "John Doe" // optional
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Created successfully",
  "data": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "johndoe",
    "name": "John Doe",
    "system_role": "user",
    "is_active": true,
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00"
  }
}
```

### POST /auth/login
Authenticate user and get access tokens.

**Request Body (Form Data):**
```
username: user@example.com (or username)
password: password123
```

**Response:**
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "johndoe",
    "name": "John Doe",
    "system_role": "user",
    "is_active": true,
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00"
  }
}
```

### POST /auth/refresh-token
Refresh access token using refresh token.

**Authentication:** None (uses refresh token)

**Request Body:**
```json
{
  "refresh_token": "your_refresh_token"
}
```

**Response:** Same as login response

### POST /auth/logout
Logout current user.

**Authentication:** Required

**Response:**
```json
{
  "code": 200,
  "message": "Logout successful"
}
```

### PUT /auth/reset-password
Change user password.

**Authentication:** Required

**Request Body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Password updated successfully"
}
```

---

## 2. User Management Endpoints

### GET /users/profile
Get current user's profile information.

**Authentication:** Required

**Response:**
```json
{
  "code": 200,
  "message": "Profile retrieved successfully",
  "data": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "johndoe",
    "name": "John Doe",
    "system_role": "user",
    "is_active": true,
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00",
    "last_login": "2024-01-01 12:00:00"
  }
}
```

### PUT /users/profile
Update current user's profile.

**Authentication:** Required

**Request Body:**
```json
{
  "email": "newemail@example.com", // optional
  "name": "New Name" // optional
}
```

### POST /users/admin/view-all-users
Get all users (admin only).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "name_filter": "John", // optional
  "email_filter": "example.com", // optional
  "page": 1,
  "limit": 10
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Users retrieved successfully",
  "data": [
    {
      "id": "user_id",
      "email": "user@example.com",
      "username": "johndoe",
      "name": "John Doe",
      "system_role": "user",
      "is_active": true,
      "created_at": "2024-01-01 00:00:00",
      "updated_at": "2024-01-01 00:00:00",
      "last_login": "2024-01-01 12:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

### POST /users/admin/grant-role
Grant system role to user (admin only).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "user_id": "target_user_id",
  "system_role": "creator" // "admin" | "creator" | "user"
}
```

---

## 3. Group Management Endpoints

### POST /groups/create-group
Create a new group.

**Authentication:** Required (Creator or Admin role)

**Request Body:**
```json
{
  "group_name": "My Group",
  "description": "Group description", // optional
  "is_public": false, // optional, default false
  "is_hidden": false // optional, default false
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Group created successfully",
  "data": {
    "id": "group_id",
    "group_name": "My Group",
    "description": "Group description",
    "manager_id": "user_id",
    "is_public": false,
    "is_hidden": false,
    "num_member": 1,
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00"
  }
}
```

### POST /groups/modify-group
Modify group information.

**Authentication:** Required (Group admin only)

**Request Body:**
```json
{
  "group_id": "group_id",
  "group_name": "New Group Name", // optional
  "description": "New description", // optional
  "is_public": true, // optional
  "is_hidden": false // optional
}
```

### POST /groups/get-list-group-you-created
Get groups created by current user.

**Authentication:** Required

**Response:**
```json
{
  "code": 200,
  "message": "Groups retrieved successfully",
  "data": [
    {
      "id": "group_id",
      "group_name": "My Group",
      "description": "Group description",
      "manager_id": "user_id",
      "is_public": false,
      "is_hidden": false,
      "num_member": 5,
      "created_at": "2024-01-01 00:00:00",
      "updated_at": "2024-01-01 00:00:00"
    }
  ],
  "total": 1
}
```

### POST /groups/get-list-group-shared-you
Get groups shared with current user.

**Authentication:** Required

### POST /groups/get-list-group-community
Get public groups.

**Authentication:** Required

### POST /groups/add-member
Add member to group.

**Authentication:** Required

**Request Body:**
```json
{
  "group_id": "group_id",
  "email": "member@example.com"
}
```

### POST /groups/remove-member
Remove member from group.

**Authentication:** Required (Group admin only)

**Request Body:**
```json
{
  "group_id": "group_id",
  "email": "member@example.com"
}
```

### POST /groups/view-users-in-group
View users in group.

**Authentication:** Required (Group member)

**Request Body:**
```json
{
  "group_id": "group_id"
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Users retrieved successfully",
  "data": [
    {
      "name": "John Doe",
      "email": "john@example.com"
    }
  ]
}
```

### POST /groups/remove-group
Remove/delete group.

**Authentication:** Required (Group admin only)

**Request Body:**
```json
{
  "group_id": "group_id"
}
```

---

## 4. Collection Management Endpoints

### POST /collections/new-collection
Create a new document collection.

**Authentication:** Required (Creator or Admin role)

**Request Body:**
```json
{
  "collection_name": "My Collection",
  "description": "Collection description", // optional
  "status": "active", // optional, default "active"
  "tags": ["tag1", "tag2"], // optional
  "is_public": false, // optional, default false
  "is_hidden": false // optional, default false
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Created successfully",
  "data": {
    "collection_id": "collection_id",
    "collection_name": "My Collection",
    "user_id": "user_id",
    "role": "owner",
    "status": "active",
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00",
    "document_count": 0,
    "total_size_bytes": 0,
    "description": "Collection description",
    "tags": ["tag1", "tag2"]
  }
}
```

### POST /collections/modify-collection
Modify collection settings.

**Authentication:** Required (Collection owner)

**Request Body:**
```json
{
  "collection_id": "collection_id",
  "collection_name": "New Collection Name", // optional
  "is_public": true, // optional
  "is_hidden": false // optional
}
```

### POST /collections/get-list-collection-you-created
Get collections created by current user.

**Authentication:** Required

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "collection_id": "collection_id",
      "collection_name": "My Collection",
      "user_id": "user_id",
      "role": "owner",
      "status": "active",
      "created_at": "2024-01-01 00:00:00",
      "updated_at": "2024-01-01 00:00:00",
      "document_count": 5,
      "total_size_bytes": 1024000,
      "description": "Collection description",
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 1
}
```

### POST /collections/get-list-collection-shared-you
Get collections shared with current user.

**Authentication:** Required

### POST /collections/get-list-collection-community
Get public collections.

**Authentication:** Required

**Request Body:**
```json
{
  "search_name": "search term" // optional
}
```

### POST /collections/share
Share collection with specific user.

**Authentication:** Required (Collection owner)

**Request Body:**
```json
{
  "collection_id": "collection_id",
  "user_email": "user@example.com",
  "role": "viewer" // "editor" | "viewer"
}
```

### POST /collections/shares
Share collection with group members.

**Authentication:** Required (Collection owner)

**Request Body:**
```json
{
  "collection_id": "collection_id",
  "group_id": "group_id",
  "role": "viewer" // "editor" | "viewer"
}
```

### POST /collections/delete-collection
Delete a collection.

**Authentication:** Required (Collection owner)

**Request Body:**
```json
{
  "collection_id": "collection_id"
}
```

---

## 5. Document Management Endpoints

### POST /documents/add-document
Upload a document to a collection.

**Authentication:** Required (Collection editor or owner)

**Request Body (Form Data):**
```
file: <file_upload>
collection_id: "collection_id"
description: "Document description" (optional)
file_type: "pdf" (optional, auto-detected if not provided)
file_name: "custom_name.pdf" (optional, uses original if not provided)
```

**Response:**
```json
{
  "code": 200,
  "message": "Updated successfully",
  "data": {
    "fileId": "file_id",
    "fileName": "document.pdf",
    "fileType": "pdf",
    "status": "pending",
    "userId": "user_id",
    "collectionId": "collection_id",
    "createdAt": "01/01/2024 00:00:00",
    "updatedAt": "01/01/2024 00:00:00",
    "processResult": ""
  }
}
```

### POST /documents/get-list-docs-collection
Get documents in a collection.

**Authentication:** Required (Collection access)

**Request Body:**
```json
{
  "collection_id": "collection_id",
  "file_types": ["pdf", "docx"], // optional
  "status": ["completed", "pending"], // optional
  "created_after": "2024-01-01T00:00:00", // optional
  "created_before": "2024-12-31T23:59:59" // optional
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "fileId": "file_id",
      "fileName": "document.pdf",
      "fileType": "pdf",
      "status": "completed",
      "userId": "user_id",
      "collectionId": "collection_id",
      "createdAt": "01/01/2024 00:00:00",
      "updatedAt": "01/01/2024 00:00:00",
      "processResult": "Successfully processed"
    }
  ],
  "total": 1
}
```

### POST /documents/delete-file
Delete a document from collection.

**Authentication:** Required (Collection editor or owner)

**Request Body:**
```json
{
  "collection_id": "collection_id",
  "file_id": "file_id"
}
```

### POST /documents/download-file
Download a document.

**Authentication:** Required (Collection access)

**Request Body (Form Data):**
```
collection_id: "collection_id"
file_id: "file_id"
```

**Response:** File stream download

---

## 6. Chat Endpoints

### GET /chats/list-chats
Get user's chat history list.

**Authentication:** Required

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": "chat_id",
      "title": "Chat about AI",
      "update_at": "1704067200"
    }
  ],
  "total": 1
}
```

### POST /chats/chat-history/{chatId}
Get specific chat conversation history.

**Authentication:** Required

**Path Parameter:**
- `chatId`: Chat ID

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "chat_id": "chat_id",
    "history": [
      ["user", "Hello, how are you?"],
      ["assistant", "I'm doing well, thank you! How can I help you today?"]
    ]
  },
  "total": 2
}
```

### POST /chats/delete-chat/{chatId}
Delete a chat conversation.

**Authentication:** Required

**Path Parameter:**
- `chatId`: Chat ID

**Response:**
```json
{
  "code": 200,
  "message": "Success"
}
```

### PUT /chats/rename-chat
Rename a chat conversation.

**Authentication:** Required

**Request Body:**
```json
{
  "chat_id": "chat_id",
  "new_title": "New Chat Title"
}
```

### WebSocket /chats/chat-stream
Real-time chat streaming endpoint.

**Authentication:** Required (via query parameter or connection header)

**Connection:** `ws://localhost:8000/chats/chat-stream`

**Send Message Format:**
```json
{
  "question": "Your question here",
  "modelName": "gpt-3.5-turbo",
  "chatId": "existing_chat_id", // optional for new chat
  "collectionId": "collection_id", // optional for RAG
  "fileIds": ["file_id1", "file_id2"] // optional for specific files
}
```

**Receive Message Formats:**
```json
// Answer chunks (streaming)
{"type": "answer_chunk", "data": "partial answer text"}

// End of answer
{"type": "end_chunk", "data": "[END]"}

// Source documents
{"type": "source", "data": [{"title": "doc.pdf", "content": "relevant text"}]}

// Chat ID (for new chats)
{"type": "chatId", "data": "new_chat_id"}

// Errors
{"type": "error", "data": "Error message"}
```

---

## Error Responses

### Common Error Codes
- `400` - Bad Request (missing fields, validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "code": 400,
  "message": "Missing required field: email",
  "data": null
}
```

---

## Frontend Integration Guide

### Authentication Flow
1. **Login:** Call `/auth/login` → Store access/refresh tokens
2. **API Calls:** Include `Authorization: Bearer <access_token>` header
3. **Token Refresh:** When token expires, call `/auth/refresh-token`
4. **Logout:** Call `/auth/logout` → Clear stored tokens

### Chat Interface Requirements
1. **Chat List:** Use `/chats/list-chats` to show user's conversations
2. **Chat History:** Use `/chats/chat-history/{chatId}` to load conversation
3. **Real-time Chat:** Connect to WebSocket `/chats/chat-stream`
4. **Chat Management:** Rename with `/chats/rename-chat`, delete with `/chats/delete-chat`

### Document Management Interface
1. **Collections:** List user's collections with appropriate endpoints
2. **File Upload:** Use `/documents/add-document` with FormData
3. **File List:** Show collection documents with `/documents/get-list-docs-collection`
4. **File Actions:** Download, delete files with respective endpoints

### Group & Sharing Interface
1. **Group Management:** Create, modify, delete groups
2. **Member Management:** Add/remove group members
3. **Collection Sharing:** Share collections with users or groups

### Recommended State Management
- User authentication state (token, user info)
- Active chat/collection context
- Real-time WebSocket connection status
- File upload progress
- Error/success notifications

### WebSocket Integration Example (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/chats/chat-stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    question: "Hello, AI!",
    modelName: "gpt-3.5-turbo",
    chatId: "existing_chat_id" // optional
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch(message.type) {
    case 'answer_chunk':
      // Append to chat display
      break;
    case 'source':
      // Show source documents
      break;
    case 'chatId':
      // Save new chat ID
      break;
    case 'error':
      // Handle error
      break;
  }
};
```

This documentation provides all the necessary information to build a comprehensive frontend for your chatbot application.
