# MX-Soft Distr — Bildirishnomalar API

**Base URL:** `http://<host>:8002/api/v1/notifications`

---

## 1. Bildirishnoma yaratish (ochiq)

```
POST /api/v1/notifications/create
```

Security kalit yoki company_id orqali FCM push xabarlar yuborish. `users_1c_id` ro'yxati bo'yicha har bir foydalanuvchiga Firebase orqali push yuboriladi.

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| title | string (max 250) | Ha | Sarlavha |
| message | string (max 2000) | Yo'q | Xabar matni |
| date | string (max 10) | Yo'q | Sana (DD.MM.YYYY) |
| author | string (max 100) | Yo'q | Muallif |
| user_type | string (max 50) | Yo'q | Foydalanuvchi turi |
| user_1c_id | int | Yo'q | Bitta foydalanuvchi 1C ID |
| company_id | int | Yo'q | Kompaniya ID |
| security_key | string (max 255) | Yo'q | Security kalit (tekshiriladi) |
| users_1c_id | List[int] | Yo'q | Bir nechta foydalanuvchi 1C ID ro'yxati |

> Agar `users_1c_id` berilmasa, `user_1c_id` ishlatiladi. Security kalit bo'lsa, `company_id` avtomatik aniqlanadi.

**Response (201):**
```json
{
  "id": 1,
  "company_id": 1,
  "user_1c_id": 100,
  "created_at": "2024-01-01T12:00:00",
  "title": "Yangi buyurtma",
  "message": "Sizga yangi buyurtma biriktirildi",
  "status": null,
  "author": "Admin"
}
```

**Xatoliklar:** `400` — Invalid security key | `404` — Company not found

---

## 2. Foydalanuvchiga xabar yuborish (admin)

```
POST /api/v1/notifications/send-to-user
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| user_id | int | Ha | DB user ID |
| title | string (max 250) | Ha | Sarlavha |
| message | string (max 2000) | Yo'q | Xabar matni |
| date | string (max 10) | Yo'q | Sana |
| author | string (max 100) | Yo'q | Muallif |

**Response (201):** `NotificationResponse`

> Avtomatik ravishda `NotificationUserStatus` yaratiladi va FCM orqali push yuboriladi.

**Xatoliklar:** `404` — Target user not found | `403` — Only admins

---

## 3. 1C ID bo'yicha xabar yuborish (admin)

```
POST /api/v1/notifications/send-to-user-1c
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| user_1c_id | int | Ha | 1C tizim ID |
| company_id | int | Yo'q | Kompaniya bo'yicha cheklash |
| title | string (max 250) | Ha | Sarlavha |
| message | string (max 2000) | Yo'q | Xabar matni |
| date | string (max 10) | Yo'q | Sana |
| author | string (max 100) | Yo'q | Muallif |

**Xatoliklar:** `404` — Target user not found

---

## 4. Security kalit orqali xabar yuborish

```
POST /api/v1/notifications/send-by-key
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| security_key | string (max 255) | Ha | Xavfsizlik kaliti |
| user_1c_id | int | Ha | 1C ID |
| title | string (max 250) | Ha | Sarlavha |
| message | string (max 2000) | Yo'q | Xabar matni |
| date | string (max 10) | Yo'q | Sana |
| author | string (max 100) | Yo'q | Muallif |

**Xatoliklar:** `400` — Invalid security key | `404` — Target user not found

---

## 5. Bildirishnomalar ro'yxati

```
GET /api/v1/notifications
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| company_id | int | Yo'q | Kompaniya bo'yicha filtrlash |
| user_1c_id | int | Yo'q | 1C ID bo'yicha filtrlash |

**Response (200):**
```json
[
  {
    "id": 1,
    "company_id": 1,
    "user_1c_id": 100,
    "created_at": "2024-01-01T12:00:00",
    "title": "Yangi buyurtma",
    "message": "Sizga yangi buyurtma biriktirildi",
    "status": {
      "id": 1,
      "is_read": false,
      "read_at": null
    },
    "author": "Admin"
  }
]
```

---

## 6. Joriy foydalanuvchi bildirishnomalari

```
GET /api/v1/notifications/user
```

Joriy auth foydalanuvchining `user_1c_id` bo'yicha barcha bildirishnomalarini qaytaradi.

**Response (200):** `List[NotificationResponse]`

---

## 7. Bitta bildirishnoma

```
GET /api/v1/notifications/{notification_id}
```

**Xatoliklar:** `404` — Notification not found

---

## 8. Bildirishnoma o'chirish

```
DELETE /api/v1/notifications/{notification_id}
```

**Response:** `204 No Content`

**Xatoliklar:** `404` — Notification not found

---

## 9. Kompaniya bildirishnomalari

```
GET /api/v1/notifications/company/{company_id}
```

**Response (200):** `List[NotificationResponse]`

---

## 10. Bildirishnomani o'qilgan deb belgilash

```
POST /api/v1/notifications/{notification_id}/read
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Path** ||||
| notification_id | int | Ha | Bildirishnoma ID |

**Response (200):**
```json
{
  "id": 1,
  "notification_id": 1,
  "user_id": 1,
  "is_read": true,
  "read_at": "2024-01-01T12:05:00",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:05:00"
}
```

> Agar status mavjud bo'lmasa, yangisi yaratiladi.

---

## 11. O'qilmaganlar soni

```
GET /api/v1/notifications/unread-count
```

**Response (200):**
```json
{
  "unread_count": 5
}
```

---

## 12. Bir nechtasini o'qilgan deb belgilash

```
POST /api/v1/notifications/read-multiple
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| - | List[int] | Ha | Bildirishnoma ID lar ro'yxati |

Masalan: `[1, 2, 3, 5, 8]`

**Response (200):**
```json
{
  "message": "Marked 5 as read"
}
```

---

## 13. Firebase config yuklash

```
POST /api/v1/notifications/firebase-config
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| file | file | Ha | Firebase service account JSON fayl |

Talab qilinadigan JSON maydonlari:
- `project_id`
- `private_key_id`
- `private_key`
- `client_email`

**Response (200):**
```json
{
  "message": "Firebase config updated successfully",
  "project_id": "my-project"
}
```

**Xatoliklar:** `400` — Invalid JSON / Missing required fields | `403` — Only admins
