# Working Session Tracking API

## Overview
The Working Session Tracking API allows you to manage working sessions for users. A working session records when a user works on a specific device on a given date.

## Base URL
```
/api/v1/working-sessions
```

## Authentication
All endpoints require authentication. Use one of the following methods:
- **OAuth2 Token**: Include in the Authorization header: `Bearer <token>`
- **API Key**: Include in the X-API-KEY header: `X-API-KEY: <api-key>`

## Data Models

### WorkingSessionCreate
```json
{
    "session": "2026-04-24",
    "device_name": "DEVICE-001",
    "user_id": 1
}
```

### WorkingSessionUpdate
```json
{
    "session": "2026-04-25",
    "device_name": "DEVICE-002",
    "user_id": 2
}
```

### WorkingSessionResponse
```json
{
    "id": 1,
    "session": "2026-04-24",
    "device_name": "DEVICE-001",
    "user_id": 1,
    "created_at": "2026-04-24T10:30:00"
}
```

## Endpoints

### 1. Create a Working Session
Creates a new working session record.

**Request:**
```http
POST /api/v1/working-sessions
Content-Type: application/json
Authorization: Bearer <your-token>
```

**Body:**
```json
{
    "session": "2026-04-24",
    "device_name": "DEVICE-001",
    "user_id": 1
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "session": "2026-04-24",
    "device_name": "DEVICE-001",
    "user_id": 1,
    "created_at": "2026-04-24T10:30:00"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/working-sessions" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "session": "2026-04-24",
    "device_name": "DEVICE-001",
    "user_id": 1
  }'
```

---

### 2. List All Working Sessions
Retrieves a list of all working sessions.

**Request:**
```http
GET /api/v1/working-sessions
Authorization: Bearer <your-token>
```

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "session": "2026-04-24",
        "device_name": "DEVICE-001",
        "user_id": 1,
        "created_at": "2026-04-24T10:30:00"
    },
    {
        "id": 2,
        "session": "2026-04-24",
        "device_name": "DEVICE-002",
        "user_id": 2,
        "created_at": "2026-04-24T11:00:00"
    }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/working-sessions" \
  -H "Authorization: Bearer <your-token>"
```

---

### 3. Get a Specific Working Session
Retrieves a single working session by its ID.

**Request:**
```http
GET /api/v1/working-sessions/{session_id}
Authorization: Bearer <your-token>
```

**Response (200 OK):**
```json
{
    "id": 1,
    "session": "2026-04-24",
    "device_name": "DEVICE-001",
    "user_id": 1,
    "created_at": "2026-04-24T10:30:00"
}
```

**Error Response (404 Not Found):**
```json
{
    "detail": "Working session not found"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/working-sessions/1" \
  -H "Authorization: Bearer <your-token>"
```

---

### 4. Get Working Sessions by User
Retrieves all working sessions for a specific user, ordered by session date (descending).

**Request:**
```http
GET /api/v1/working-sessions/user/{user_id}
Authorization: Bearer <your-token>
```

**Response (200 OK):**
```json
[
    {
        "id": 3,
        "session": "2026-04-24",
        "device_name": "DEVICE-001",
        "user_id": 1,
        "created_at": "2026-04-24T10:30:00"
    },
    {
        "id": 1,
        "session": "2026-04-23",
        "device_name": "DEVICE-001",
        "user_id": 1,
        "created_at": "2026-04-23T09:00:00"
    }
]
```

**Error Response (404 Not Found):**
```json
{
    "detail": "User not found"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/working-sessions/user/1" \
  -H "Authorization: Bearer <your-token>"
```

---

### 5. Update a Working Session
Updates an existing working session. Only provide the fields you want to update.

**Request:**
```http
PATCH /api/v1/working-sessions/{session_id}
Content-Type: application/json
Authorization: Bearer <your-token>
```

**Body (all fields optional):**
```json
{
    "session": "2026-04-25",
    "device_name": "DEVICE-UPDATED",
    "user_id": 2
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "session": "2026-04-25",
    "device_name": "DEVICE-UPDATED",
    "user_id": 2,
    "created_at": "2026-04-24T10:30:00"
}
```

**Error Responses:**
- **404 Not Found**: `{"detail": "Working session not found"}`
- **404 Not Found**: `{"detail": "User not found"}` (if updating user_id to non-existent user)

**cURL Example:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/working-sessions/1" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "DEVICE-UPDATED"
  }'
```

---

### 6. Delete a Working Session
Deletes a working session by its ID.

**Request:**
```http
DELETE /api/v1/working-sessions/{session_id}
Authorization: Bearer <your-token>
```

**Response (204 No Content):**
No body returned.

**Error Response (404 Not Found):**
```json
{
    "detail": "Working session not found"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/working-sessions/1" \
  -H "Authorization: Bearer <your-token>"
```

---

## Admin Panel
The Working Session admin interface is available at:
```
/admin/working-session
```

Features:
- View all working sessions in a tabular format
- Search by device name
- Sort by user
- Create, edit, and delete working sessions through the UI

---

## Notes
- The `session` field represents the date of the working session (format: YYYY-MM-DD)
- The `device_name` field stores the name/identifier of the device used
- The `user_id` must correspond to an existing user in the system
- All timestamps are in UTC
- Authentication is required for all endpoints
