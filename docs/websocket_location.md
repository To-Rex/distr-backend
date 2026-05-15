# WebSocket Location API

## Overview

Agents can send their GPS location to the server via WebSocket. The location is persisted to the database and broadcasted to connected supervisors.

## WebSocket Endpoint

```
ws://127.0.0.1:8000/ws?token={jwt_token}
```

Example:
```
ws://127.0.0.1:8000/ws?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Sending Location

Send a JSON message with the `set_location` action:

```json
{
  "action": "set_location",
  "latitude": 41.2044,
  "longitude": 74.7662,
  "timestamp": "2026-04-06T18:37:13Z"
}
```

## Response

On success:

```json
{
  "action": "location_set",
  "agent_id": 123,
  "status": "ok"
}
```

On error:

```json
{
  "action": "error",
  "message": "Invalid data"
}
```

## Flow

1. Agent connects via WebSocket with JWT token
2. Agent sends `set_location` message with latitude, longitude, timestamp
3. Server saves location to `locations` table
4. Server broadcasts location update to all connected supervisors

## Supervisor Notification

Supervisors receive agent location updates:

```json
{
  "action": "location_update",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+996555123456",
    "role": "agent"
  },
  "latitude": 41.2044,
  "longitude": 74.7662,
  "timestamp": "2026-04-06T18:37:13Z"
}
```

## Manager Notification

Managers receive supervisor location updates (same format, with role: "supervisor"):

```json
{
  "action": "location_update",
  "user": {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+996555654321",
    "role": "supervisor"
  },
  "latitude": 41.2044,
  "longitude": 74.7662,
  "timestamp": "2026-04-06T18:37:13Z"
}
```

## Admin Notification

Admins receive manager location updates (same format, with role: "manager"):

```json
{
  "action": "location_update",
  "user": {
    "id": 3,
    "first_name": "Admin",
    "last_name": "User",
    "phone_number": "+996555999999",
    "role": "manager"
  },
  "latitude": 41.2044,
  "longitude": 74.7662,
  "timestamp": "2026-04-06T18:37:13Z"
}
```