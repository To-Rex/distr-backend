# MX-Soft Distr — Faoliyat (Activity) va Database Backup API

---

## Faoliyatlar (`/api/v1/activity`)

### Faoliyatlar ro'yxati

```
GET /api/v1/activity?lang=uz
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| lang | string | Yo'q (uz) | Til: `uz`, `ru` yoki `en` |

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "action": "user_registered",
      "message_uz": "Foydalanuvchi ro'yxatdan o'tdi admin",
      "message_ru": "Пользователь зарегистрирован admin",
      "message_en": "User registered admin",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

---

## Ma'lumotlar Bazasi Backup (`/api/v1/database`)

### 1. Eksport (pg_dump)

```
GET /api/v1/database/export
```

| Ruxsat: faqat SUPERADMIN ||

PostgreSQL bazasini `.dump` formatda eksport qiladi. Fayl yuklab olinadi va avtomatik MinIO ga ham yuklanadi.

**Response (200):** Binary `.dump` fayl (FileResponse)

**Xatoliklar:** `403` — Only superadmin | `500` — pg_dump not found / export failed

---

### 2. Import (pg_restore)

```
POST /api/v1/database/import
```

| Ruxsat: faqat SUPERADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| file | file | Ha | `.dump` formatdagi fayl |

> **Eslatma:** Import qilishdan oldin joriy `public` schema o'chiriladi va yangisi yaratiladi! Timeout: 10 daqiqa.

**Response (200):**
```json
{
  "message": "Database imported successfully"
}
```

**Xatoliklar:** `400` — File must have .dump extension | `403` — Only superadmin | `504` — Timeout (10 min) | `500` — pg_restore failed

---

### 3. Parol orqali import

```
POST /api/v1/database/import/by-password
```

Auth o'rniga parol orqali import. SUPERADMIN ruxsati talab qilinmaydi.

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| file | file | Ha | `.dump` fayl |
| password | string | Ha | Import paroli |

**Xatoliklar:** `403` — Invalid password | Boshqa xatoliklar yuqoridagi bilan bir xil

---

## Alembic Versiya (`/api/v1/admin/alembic-version`)

| Ruxsat: faqat SUPERADMIN ||

### 1. Versiyalar ro'yxati

```
GET /api/v1/admin/alembic-version/list
```

**Response (200):**
```json
[
  { "version_num": "abc123def456" },
  { "version_num": "789ghi012jkl" }
]
```

---

### 2. Versiya yaratish

```
POST /api/v1/admin/alembic-version/create
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| version_num | string (max 32) | Ha | Migration versiya raqami |

**Response (201):** `{ "version_num": "abc123def456" }`

**Xatoliklar:** `400` — Version already exists | `403` — Only superadmin

---

### 3. Versiya o'chirish

```
DELETE /api/v1/admin/alembic-version/{version_num}
```

**Response:** `204 No Content`

**Xatoliklar:** `404` — Version not found | `403` — Only superadmin
