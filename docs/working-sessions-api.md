# MX-Soft Distr — Ish Sessiyalari API

**Base URL:** `http://<host>:8002/api/v1/working-sessions`

Ish sessiyalari — xodimlarning ilovada ishlash faoliyatini kuzatish (har bir sessiya = ilova ochilishi).

---

## 1. Ish sessiyasi yaratish

```
POST /api/v1/working-sessions/create
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| session | datetime | Ha | Sessiya vaqti |
| device_name | string | Ha | Qurilma nomi |
| app | string | Ha | Ilova nomi |
| is_testing | bool | Yo'q (false) | Test rejimi |

**Response (201):**
```json
{
  "id": 1,
  "session": "2024-01-01T09:00:00",
  "device_name": "Samsung A52",
  "app": "MXAgent",
  "is_testing": false,
  "created_at": "2024-01-01T09:00:00"
}
```

**Xatoliklar:** `404` — User not found

---

## 2. Bugungi sessiyalar ro'yxati

```
GET /api/v1/working-sessions
```

Bugungi kundagi har bir xodim uchun **eng birinchi** sessiyani qaytaradi. Joriy foydalanuvchining `company_id` ga tegishli xodimlar.

**Response (200):**
```json
[
  {
    "user": {
      "id": 1,
      "username": "agent1",
      "email": "agent1@example.com",
      "first_name": "Ali",
      "last_name": "Valiyev",
      "phone_number": "+998901234567",
      "photo": null,
      "user_type": "AGENT",
      "company_id": 1,
      "branch_id": 1,
      "company_rel": { "id": 1, "name": "My Company", ... },
      "branch_rel": { "id": 1, "name": "Toshkent", ... },
      "manager": null,
      "manager_id": null,
      "user_1c_id": 100,
      "created_at": "2024-01-01T00:00:00",
      "user_status": "ACTIVE"
    },
    "session": {
      "id": 1,
      "session": "2024-01-01T09:00:00",
      "device_name": "Samsung A52",
      "app": "MXAgent",
      "is_testing": false,
      "created_at": "2024-01-01T09:00:00"
    }
  }
]
```

---

## 3. Bitta sessiya

```
GET /api/v1/working-sessions/{session_id}
```

**Response (200):** `WorkingSessionResponse`

**Xatoliklar:** `404` — Working session not found

---

## 4. Foydalanuvchi sessiyalari

```
GET /api/v1/working-sessions/user/{user_id}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Path** ||||
| user_id | int | Ha | Foydalanuvchi ID |
| **Query** ||||
| app | string | Yo'q | Ilova bo'yicha filtrlash |
| is_testing | bool | Yo'q | Test sessiyalarni filtrlash |

> `app=mx-manager` bo'lsa filtr qo'llanilmaydi (barcha ilovalar qaytariladi).

**Response (200):** `List[WorkingSessionResponse]` — Yangidan eskiga tartiblangan

**Xatoliklar:** `404` — User not found

---

## 5. Sessiyani o'chirish

```
DELETE /api/v1/working-sessions/{session_id}
```

**Response:** `204 No Content`

**Xatoliklar:** `404` — Working session not found
