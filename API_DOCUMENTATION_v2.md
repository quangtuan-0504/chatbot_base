# Chatbot API Documentation

## Overview
This document provides comprehensive API documentation for the Chatbot application. The API follows REST principles and uses JWT tokens for authentication.

**Base URL:** `http://127.0.0.1:8050/api/v1` (adjust according to your deployment)

## Authentication
All endpoints except `/auth/register` and `/auth/login` require JWT authentication. Include the token in the Authorization header:
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
**Response:** Same as **GET** /users/profile response

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
**Response:** Same as **GET** /users/profile response

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
**Response:** Same as **POST** /groups/create-group response

### POST /groups/get-list-group-you-created
Get groups created by current user.

**Authentication:** Required

**Request Body:**
```json
{
  "group_name": "search term", // optional
}
```

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

**Request Body:**
```json
{
  "group_name": "search term", // optional
}
```

**Response:** Same as **POST** /groups/get-list-group-you-created response

### POST /groups/get-list-group-community
Get public groups.

**Authentication:** Required

**Request Body:**
```json
{
  "group_name": "search term", // optional
}
```

**Response:** Same as **POST** /groups/get-list-group-you-created response

### POST /groups/admin/view-all-groups
Get all users (admin only).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "group_name_filter": "group name", // optional
  "num_member_filter": "5", // optional
  "page": 1,
  "limit": 10
}
```

**Response:** Same as **POST** /groups/get-list-group-you-created response

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
**Response:**
```json
{
  "code": 200,
  "message": "Member added successfully",
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
**Response:** Same as **POST** /groups/add-member response

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
**Response:** Same as **POST** /groups/add-member response

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
**Response:** Same as **POST** /collections/new-collection response
### POST /collections/get-list-collection-you-created
Get collections created by current user.

**Authentication:** Required

**Request Body:**
```json
{
  "collection_name": "search term", // optional
}
```

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

**Request Body:**
```json
{
  "collection_name": "search term", // optional
  "roles": ["editor", "viewer"]
}
```

**Response:** Same as **POST** /collections/get-list-collection-you-created response
### POST /collections/get-list-collection-community
Get public collections.

**Authentication:** Required

**Request Body:**
```json
{
  "search_name": "search term" // optional
}
```

**Response:** Same as **POST** /collections/get-list-collection-you-created response
### POST /groups/admin/view-all-collections
Get all users (admin only).

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "collection_name": "search term", // optional
  "status": "active", // optional
  "created_after": 1,
  "created_before": 10
}
```

**Response:** Same as **POST** /collections/get-list-collection-you-created 

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
    "file_id": "file_id",
    "file_name": "document.pdf",
    "file_type": "pdf",
    "status": "pending",
    "user_id": "user_id",
    "collection_id": "collection_id",
    "created_at": "01/01/2024 00:00:00",
    "updated_at": "01/01/2024 00:00:00",
    "process_result": ""
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
      "file_id": "file_id",
      "file_name": "document.pdf",
      "file_type": "pdf",
      "status": "completed",
      "user_id": "user_id",
      "collection_id": "collection_id",
      "created_at": "01/01/2024 00:00:00",
      "updated_at": "01/01/2024 00:00:00",
      "process_result": "Successfully processed"
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

**Query Parameters:**
- `search` (optional): Search term to filter chats by title

**Examples:**
- Get all chats: `GET /chats/list-chats`
- Search chats: `GET /chats/list-chats?search=AI`

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": "chat_id",
      "title": "Chat about AI",
      "update_at": "01/01/2024 00:00:00"
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
                {
                  "role": "user",
                  "content": 
                  {
                    "message": [
                        {"type": "text", "text": "question"},
                        {"type": "image_url", "image_url": "data:image/jpeg;base64,{image_base64}"},
                        {"type": "image_url", "image_url": "data:image/jpeg;base64,{image_base64}"}
                    ],
                  }
                },
                {
                  "role": "assistant", 
                  "content": 
                  {
                    "message": [
                        {"type": "text", "text": "answer"},
                    ],
                    "source": [{"file_id" : "file id", "file_name" : "file name"}],
                    "collection_id": "collection id"
                  }
                }
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

**Connection:** `ws://127.0.0.1:8050/api/v1/chats/chat-stream`

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
{"type": "source", "data": [{"file_name": "doc.pdf", "file_id": "file_id"}]}

// Chat ID (for new chats)
{"type": "chat_id", "data": "new_chat_id"}

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
Ban đầu sẽ hiển thị trang gốc, mô tả các tính năng và hướng dẫn sơ bộ cách sử dụng chatbot này. Trang này có nút get start , khi user nhấn vô sẽ chuyển sang trang đăng nhập đăng kí. user đăng nhập thành công sẽ chuyển sang trang để chat.

1. **Login:** Call `/auth/login` → Store access/refresh tokens
2. **API Calls:** Include `Authorization: Bearer <access_token>` header
3. **Token Refresh:** When token expires, call `/auth/refresh-token`
4. **Logout:** Call `/auth/logout` → Clear stored tokens
5. **Reset password** Call `/auth/reset-password` → Reset password

### Giao diện chính ứng dụng Chatbot

Gồm hai phần chính: **thanh bên trái (sidebar)** và **khu vực chính (main chat area)**.

---

#### 🧭 Thanh bên trái (Sidebar)

> Nằm cố định ở cạnh trái màn hình, chia thành nhiều khu vực chức năng.

##### 1. Thanh điều hướng trên cùng

- Nút **"Home"** nằm ở góc trên cùng, khi nhấn vào sẽ quay trở lại trang home.  
- Bên cạnh có **Icon sidebar** (để mở/thu gọn sidebar).  

---

##### 2. Khu vực tạo và tìm kiếm hội thoại

- Nút **"New chat"** để bắt đầu cuộc trò chuyện mới.  
- Ô **"Search chat"** để tìm kiếm các cuộc trò chuyện đã có. Khi nhấn vào ô này thì giữa giao diện sẽ hiển thị Search modal để search các đoạn chat cũ, nếu nhấn vào sẽ mở lại đoạn chat cũ đó. Dùng endpoint `GET /chats/list-chats` để tìm kiếm các đoạn chat, endpoint `POST /chats/chat-history/{chatId}` để lấy lịch sử chat.

---

##### 3. Khu vực **Lịch sử chat**
  
- **Danh sách hội thoại**, Để liệt kê các đoạn hội thoại trước đó, sắp xếp theo thời gian và hiển thị thời gian, nhấn vào có thể mở lại các đoạn chat cũ. Dùng endpoint `GET /chats/list-chats` để lấy các đoạn hội thoại cũ. endpoint `POST /chats/chat-history/{chatId}` để mở cuộc hội thoại đó.

> Mỗi đoạn chat có **nút menu 3 chấm** bên phải để hiển thị các tùy chọn (xóa, đổi tên, v.v.). Dùng endpoint `POST /chats/delete-chat/{chatId}` để xóa đoạn chat. Endpoint `PUT /chats/rename-chat` để đổi tên chat.

---

##### 4. Khu vực quản lý

- **Các nút điều hướng:**
  - Collections, nhấn vào đây sẽ chuyển qua trang quản lý collection  
  - Groups  , nhấn vào đây sẽ chuyển qua trang quản lý group
  - Manager users *(dành riêng cho admin)*, nhấn vào đây sẽ chuyển qua trang quản lý user. *Manager users* chỉ hiển thị khi người dùng là admin.
---

##### 5. Mục người dùng

- **Nút “User”** ở cuối sidebar (hiển thị thông tin người dùng). Nhấn vào sẽ hiển thị ra tùy chọn **logout** hoặc **settings**.
nhấn vào settings thì sẽ hiển thị thông tin người dùng, và có thể đổi mật khẩu, chỉnh sửa hồ sơ. Dùng endpoint `GET /users/profile` để lấy profile của user và `PUT /users/profile` để chỉnh sửa thông tin user.

#### 💬 Khu vực chính (Main Chat Area)
Chiếm phần lớn màn hình bên phải.
##### 1. Dropdown select model
- Nút **"Model"** cho phép chọn mô hình chatbot. Nằm ở phía góc trái trên của khu vực chính.

##### 2. Khung nhập text
- Khi tạo new chat xuất hiện ở giữa là hộp để nhập nội dung, còn khi mở các đoạn chat cũ, hộp nhập text này sẽ ở phía dưới cuộc trò chuyện.

- Có biểu tượng “+” bên trái, nhấn vào sẽ hiển thị ra dropdown menu (để thêm tệp hoặc tính năng bổ sung Choose collection, web search, ...).
  - Khi chọn Choose collection sẽ hiển thị ra search modal để tìm và chọn collection. Sử dụng endpoint `POST /collections/get-list-collection-shared-you` để tìm collection. Sau khi chọn sẽ có button chứa tên collection ngay bên cạnh sau dấu “+” để biết collection nào đã được chọn, có dấu “X” để bỏ chọn.

- Có biểu tượng mũi tên lên (↑) bên phải (để gửi tin nhắn). Sử dụng endpoint `WebSocket /chats/chat-stream` để chat

##### 3. Vùng hiển thị nội dung đoạn chat
- Phần hiển thị nội dung của đoạn chat.
- Có nút copy cho phép copy câu trả lời, câu hỏi.
- Nếu câu trả lời có `source` đi kèm, thì cho phép người dùng chọn hoặc bỏ chọn `source` đó cho câu hỏi tiếp theo.
### Users Management Interface
- Trang này chỉ dành cho admin.
- Phần sidebar bên trái vẫn được giữ nguyên khi chuyển qua trang này.
- Giúp admin quản lý user, sử dụng endpoint `POST /users/admin/view-all-users` để tìm kiếm và lấy danh sách thông tin các user.
- Với mỗi user admin sử dụng endpoint `POST /users/admin/grant-role` để gán vai trò cho user.

### Group & Sharing Interface
Phần sidebar bên trái vẫn được giữ nguyên khi chuyển qua trang này.
#### 💬 Khu vực chính của quản lý group

Phần này chiếm phần lớn giao diện, hiển thị **nội dung chính của trang “Groups”**.

---

##### 1. Thanh công cụ trên cùng (Tabs và nút chức năng)

Bao gồm:

- **Các tab chuyển giữa các loại nhóm:**
  - `Your groups` *(tab đang chọn, nền xanh nhạt)*  , sử dụng endpoint `POST /groups/get-list-group-you-created` để tìm kiếm và lấy danh sách group.
  - `Shared you groups`  , sử dụng endpoint `POST /groups/get-list-group-shared-you` để tìm kiếm và lấy danh sách group.
  - `Community groups`, sử dụng endpoint `POST /groups/get-list-group-community` để tìm kiếm và lấy danh sách group.
  - `All`  , Chỉ có admin mới có tab này, sử dụng endpoint `POST /groups/admin/view-all-groups` để tìm kiếm và lấy danh sách group.
- **Nút “Create group”** – mở form tạo nhóm mới. sử dụng endpoint `POST /groups/create-group`

---

##### 2. Thanh tìm kiếm nhóm

- Ngay dưới thanh tab, có **ô tìm kiếm** với placeholder:  
  > `"Search by group names ..."`
- tab `All` thì có thể tìm theo số thành viên trong nhóm nữa.

---

##### 3. Danh sách nhóm (Group Cards)

Phần bên dưới là **các khối hình chữ nhật bo góc**, mỗi khối hiển thị thông tin một nhóm.

Mỗi **thẻ nhóm (Group Card)** gồm:

- **Tên nhóm (Group name)**  
- **Mô tả (Description)**  
- **Nút menu ba chấm dọc (⋮)** ở góc phải trên → mở menu tùy chọn với các hành động:
  - Nếu là tab `Your groups` or `Shared you groups` sẽ có:
    - Share
    - Details  
    - Remove
  - Nếu là tab `Community groups` sẽ có:
    - Details  
    - Join
  - Nếu là tab `all` chỉ có:
    - Details

  - Khi nhấn vào share sẽ hiện lên một khung chứa chỗ để nhập email của người muốn thêm vô group, nhấn nút add member để thêm người đó vô group. sử dụng endpoint `POST /groups/add-member`.
  - Khi nhấn details sẽ hiện lên khung chứa các thông tin của group, có thể sửa các thông tin của group, sau đó nhấn save để lưu các thay đổi. sử dụng endpoint `POST /groups/modify-group`
  - Khi nhấn remove sẽ xóa group. sử dung endpoint `POST /groups/remove-group`
  - Khi Join sẽ tự mình thêm vô group nếu group public
- Nếu nhấn vào thẻ nhóm sẽ hiển thị ra danh sách các thành viên trong nhóm, Dùng endpoint `POST /groups/view-users-in-group`. mỗi thành viên sẽ có nút remove, nhấn vào sẽ xóa thành viên đó khỏi nhóm. sử dụng endpoint `POST /groups/remove-member`

> Các nhóm được bố trí theo **dạng lưới**, tương tự giao diện quản lý nhóm của các ứng dụng cộng đồng.

---

##### 4. Form “Create Group” (Popup / Modal)

Khi nhấn **“Create group”**, hiển thị **hộp thoại tạo nhóm mới**.

**Các trường nhập:**
- Group name  
- Description  
- Tùy chọn: `is public` / `is hidden`

**Nút hành động:**
- Cancel  
- Create  

---

### Collections, Documents Management Interface
Phần sidebar bên trái vẫn được giữ nguyên khi chuyển qua trang này.
#### 💬 Khu vực chính của quản lý collection

Phần này chiếm phần lớn giao diện, hiển thị **nội dung chính của trang “Collections”**.

---

##### 1. Thanh công cụ trên cùng (Tabs và nút chức năng)

Bao gồm:

- **Các tab chuyển giữa các loại nhóm:**
  - `Your collection` *(tab đang chọn, nền xanh nhạt)*  , sử dụng endpoint `POST /collections/get-list-collection-you-created` để tìm kiếm và lấy danh sách group.
  - `Shared you collections`  , sử dụng endpoint `POST /collections/get-list-collection-shared-you` để tìm kiếm và lấy danh sách group.
  - `Community collections`, sử dụng endpoint `POST /collections/get-list-collection-community` để tìm kiếm và lấy danh sách group.
  - `All`  , Chỉ có admin mới có tab này, sử dụng endpoint `POST /groups/admin/view-all-collections` để tìm kiếm và lấy danh sách group.
- **Nút “Create collection”** – mở form tạo nhóm mới. sử dụng endpoint `POST /collections/new-collection`

---

##### 2. Thanh tìm kiếm nhóm

- Ngay dưới thanh tab, có **ô tìm kiếm** với placeholder:  
  > `"Search by collection names ..."`

---

##### 3. Danh sách collection (Collection Cards)

Phần bên dưới là **các khối hình chữ nhật bo góc**, mỗi khối hiển thị thông tin một collection.

Mỗi **thẻ Collection (Collection Card)** gồm:

- **Tên Collection (Collection name)**  
- **Mô tả (Description)**  
- **Nút menu ba chấm dọc (⋮)** ở góc phải trên → mở menu tùy chọn với các hành động:
  - Nếu là tab `Your collections` or `Shared you collections` sẽ có:
    - Share
    - Details  
    - Remove
  - Nếu là tab `Community collections` sẽ có:
    - Details  
    - Get
  - Nếu là tab `all` chỉ có:
    - Details

  - Khi nhấn vào share sẽ hiện lên một khung chứa chỗ để nhập email của một người và dropdown để chọn nhóm mà muốn chia sẻ collection cho. có dropdown để chọn vai trò khi chia sẻ. sử dụng endpoint `POST /collections/share` để chia sẻ cho một người và `POST /collections/shares` cho một nhóm.
  - Khi nhấn details sẽ hiện lên khung chứa các thông tin của collection, có thể sửa các thông tin của collection, sau đó nhấn save để lưu các thay đổi. sử dụng endpoint `POST /collections/modify-collection`
  - Khi nhấn remove sẽ xóa collection. sử dung endpoint `POST /collections/delete-collection`
  - Khi Get sẽ tự mình chia sẻ collection đó cho mình nếu collection public. sử dụng endpoint `POST /collections/share`
- Nếu nhấn vào thẻ collection sẽ hiển thị ra danh sách các file trong collection. Sử dụng endpoint `POST /documents/get-list-docs-collection`. Mỗi file sẽ có nút remove, nhấn vào sẽ xóa file đó khỏi collection, sử dụng endpoint `POST /documents/delete-file`. Mỗi file cũng sẽ có nút download để tải file về, sử dụng endpoint `POST /documents/download-file`. Có nút add file để add file mới vào collection, sử dụng endpoint `POST /documents/add-document`.

> Các collection được bố trí theo **dạng lưới**, tương tự giao diện quản lý nhóm của các ứng dụng cộng đồng.

---

##### 4. Form “Create collection” (Popup / Modal)

Khi nhấn **“Create collection”**, hiển thị **hộp thoại tạo nhóm mới**.
---


### Recommended State Management
- User authentication state (token, user info)
- Active chat/collection context
- Real-time WebSocket connection status
- File upload progress
- Error/success notifications

### WebSocket Integration Example (JavaScript)
```javascript
const add = async (text, isInitial) => {
        setIsInputDisabled(true);
        setIsThinking(true);

        try {
        const ws = new WebSocket("ws://127.0.0.1:8050/api/v1/chats/chat-stream");
        ws.onopen = () => {
            ws.send(
            JSON.stringify({
                question: text,
                chatId,
                collectionId: selectedCollection?.collection_id,
                fileIds: selectedFileNames,
                modelName: selectedModel,
            })
            );
        };
        let accumulatedText = "";
        let res_completed = {};
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data); 
            if (message.type === "answer_chunk"){
                accumulatedText += message.data;
                setAnswer(accumulatedText);
            }
            else if (message.type === "source") {
                res_completed["answer"] = accumulatedText;
                res_completed["source"] = message.data || [];
            }
            else if (message.type === "end_chunk") {
                setChatHistory((prev) => [
                    ...prev, 
                    { role: "assistant", content: { ...res_completed } },
                ]);
                setIsInputDisabled(false);
                setIsThinking(false);
                setAnswer(""); // reset answer
                formRef.current?.reset();
            } else if (message.type === "chat_id") {
                setChatId(message.data);
                ws.close();
                if (isInitial) { 
                    queryClient.invalidateQueries({ queryKey: ['userChats'] })
                }
            }
        };
        ws.onerror = (error) => {
            setIsInputDisabled(false);
            setIsThinking(false);
        };
        ws.onclose = () => {};
        } catch (err) {
        setIsInputDisabled(false);
        setIsThinking(false);
        }
    };
```

This documentation provides all the necessary information to build a comprehensive frontend for your chatbot application.
