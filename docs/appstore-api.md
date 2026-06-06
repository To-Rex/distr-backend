# MX-Soft Distr — AppStore API Dokumentatsiyasi

**Base URL:** `http://<host>:8002/appstore`

**Auth turi:** JWT Bearer Token (`Authorization: Bearer <token>`) cookie orqali refresh token bilan birga.

AppStore — mobil ilovalar do'koni. Publisherlar ilova yuklaydi, foydalanuvchilar yuklab oladi.

---

## 1. Auth (`/appstore/auth`)

### 1.1. Login

```
POST /appstore/auth/login
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| username | string | Ha | Login |
| password | string | Ha | Parol |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJ...",
    "user": {
      "id": "user-admin-001",
      "username": "admin",
      "email": "admin@torex.uz",
      "role": "admin",
      "displayName": "Admin",
      "avatar": null
    }
  }
}
```

Cookie: `refreshToken` o'rnatiladi (httponly, 7 kun).

**Xatoliklar:** `401` — Login yoki parol noto'g'ri | `503` — Storage unavailable

---

### 1.2. Logout

```
POST /appstore/auth/logout
```

Cookie `refreshToken` o'chiriladi.

---

### 1.3. Profil

```
GET /appstore/auth/me
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "user-admin-001",
    "username": "admin",
    "email": "admin@torex.uz",
    "role": "admin",
    "displayName": "Admin",
    "avatar": null,
    "createdAt": "2024-01-01"
  }
}
```

---

### 1.4. Profil yangilash

```
PUT /appstore/auth/profile
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| displayName | string | Yo'q | Yangi ism |
| avatar | file | Yo'q | Avatar rasm |

---

### 1.5. Parol almashtirish

```
PATCH /appstore/auth/change-password
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| currentPassword | string | Ha | Joriy parol |
| newPassword | string | Ha | Yangi parol |

**Xatoliklar:** `400` — Noto'g'ri joriy parol

---

### 1.6. Token yangilash

```
POST /appstore/auth/refresh
```

Cookie'dan `refreshToken` ni o'qiydi va yangi `token` qaytaradi.

**Xatoliklar:** `401` — Refresh token muddati o'tgan

---

## 2. Ommaviy Ilovalar

### 2.1. Tavsiya etilganlar

```
GET /appstore/apps/featured?limit=3
```

---

### 2.2. So'nggi yangilanganlar

```
GET /appstore/apps/recently-updated?limit=4
```

---

### 2.3. Eng yangilari

```
GET /appstore/apps/newest?limit=4
```

---

### 2.4. Qidiruv tavsiyalari

```
GET /appstore/apps/search-suggestions?q=telegram&limit=5
```

> `q` parametri kamida 2 belgidan iborat bo'lishi kerak.

---

### 2.5. Ilovalar ro'yxati

```
GET /appstore/apps?q=&category=&sort=updated&page=1&limit=20
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| q | string | Yo'q | Qidiruv so'zi |
| category | string | Yo'q | Kategoriya |
| sort | string | Yo'q (updated) | `updated`, `newest`, `downloads`, `name` |
| page | int | Yo'q (1) | Sahifa |
| limit | int | Yo'q (20) | Har sahifada |
| published | bool | Yo'q (true) | Nashr qilinganlar |

**Response (200):**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "pages": 3
  }
}
```

---

### 2.6. Bitta ilova

```
GET /appstore/apps/{app_id}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "app-abc123",
    "name": "MXAgent",
    "developer": "MX Soft",
    "shortDescription": "Agent ilovasi",
    "description": "To'liq tavsif...",
    "category": "business",
    "tags": ["agent", "sales"],
    "icon": "/appstore/uploads/icons/icon.png",
    "screenshots": ["/appstore/uploads/screenshots/1.png"],
    "published": true,
    "createdBy": "user-admin-001"
  }
}
```

**Xatoliklar:** `404` — Ilova topilmadi

---

### 2.7. Ilova versiyalari

```
GET /appstore/apps/{app_id}/versions?sort=newest&page=1&limit=20
```

**Response (200):**
```json
{
  "success": true,
  "data": [...],
  "pagination": { ... }
}
```

---

### 2.8. Bitta versiya

```
GET /appstore/apps/{app_id}/versions/{version}
```

Masalan: `GET /appstore/apps/app-abc123/versions/1.2.3`

---

### 2.9. Yuklab olish

```
GET /appstore/apps/{app_id}/versions/{version}/download
```

APK faylni `application/vnd.android.package-archive` content-type bilan streaming yuklash.

---

### 2.10. Skrinshotlar

```
GET /appstore/apps/{app_id}/screenshots
```

---

## 3. Kategoriyalar

```
GET /appstore/categories
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    { "id": "business", "name": "Biznes", "appCount": 12 },
    { "id": "tools", "name": "Asboblar", "appCount": 5 }
  ]
}
```

---

## 4. Statistika

```
GET /appstore/stats
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "totalApps": 25,
    "totalDownloads": 1500,
    "totalUsers": 10
  }
}
```

---

## 5. Fayl xizmati

```
GET /appstore/uploads/{category}/{filename}
```

Masalan: `GET /appstore/uploads/icons/app-icon.png`

Qo'llab-quvvatlanadigan formatlar: `.apk`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.zip`

---

## 6. Admin — Ilovalar (`/appstore/admin`)

**Barcha admin endpointlar JWT auth talab qiladi.** Publisher o'z ilovasini boshqaradi, admin hammasini.

### 6.1. Admin ilovalar ro'yxati

```
GET /appstore/admin/apps?page=1&limit=20&published=
```

### 6.2. Admin bitta ilova

```
GET /appstore/admin/apps/{app_id}
```

### 6.3. Ilova yaratish

```
POST /appstore/admin/apps
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| name | string | Ha | Ilova nomi |
| shortDescription | string | Ha | Qisqa tavsif |
| category | string | Ha | Kategoriya |
| developer | string | Yo'q | Ishlab chiquvchi |
| description | string | Yo'q | To'liq tavsif |
| tags | string | Yo'q | Teglar (vergul bilan) |
| published | bool | Yo'q (false) | Nashr qilish |
| icon | file | Yo'q | Ikonka rasm |

**Response (201):** Ilova obyekti

---

### 6.4. Ilova yangilash

```
PUT /appstore/admin/apps/{app_id}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** — ixtiyoriy maydonlar ||
| name | string | Yo'q | |
| developer | string | Yo'q | |
| shortDescription | string | Yo'q | |
| description | string | Yo'q | |
| category | string | Yo'q | |
| tags | string | Yo'q | Vergul bilan |
| published | bool | Yo'q | |
| icon | file | Yo'q | |

---

### 6.5. Ilova o'chirish

```
DELETE /appstore/admin/apps/{app_id}
```

---

### 6.6. Nashr holatini o'zgartirish

```
PATCH /appstore/admin/apps/{app_id}/toggle-publish
```

---

## 7. Admin — Versiyalar

### 7.1. Versiya yaratish

```
POST /appstore/admin/apps/{app_id}/versions
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| version | string | Ha | Versiya raqami |
| file | file | Ha | APK fayl (max 500MB) |
| minAndroid | string | Yo'q (8.0) | Minimal Android versiya |
| changelog | string | Yo'q | O'zgarishlar |

**Xatoliklar:** `409` — Versiya allaqachon mavjud

---

### 7.2. Versiya yangilash

```
PUT /appstore/admin/apps/{app_id}/versions/{version}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| changelog | string | Yo'q | |
| minAndroid | string | Yo'q | |
| file | file | Yo'q | Yangi APK |

---

### 7.3. Versiya o'chirish

```
DELETE /appstore/admin/apps/{app_id}/versions/{version}
```

---

## 8. Admin — Skrinshotlar

### 8.1. Skrinshot yuklash

```
POST /appstore/admin/apps/{app_id}/screenshots
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| screenshots | file(s) | Ha | Bir yoki bir nechta rasm |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "screenshots": ["url1", "url2"],
    "added": 2
  }
}
```

---

### 8.2. Skrinshot o'chirish

```
DELETE /appstore/admin/apps/{app_id}/screenshots/{index}
```

Indeks bo'yicha skrinshotni o'chiradi (0 dan boshlanadi).

---

## 9. Admin — Foydalanuvchilar

**Ruxsat:** faqat `admin` roli

### 9.1. Foydalanuvchilar ro'yxati

```
GET /appstore/admin/users?page=1&limit=20&role=&q=
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| page | int | Yo'q | |
| limit | int | Yo'q | |
| role | string | Yo'q | `admin` yoki `publisher` |
| q | string | Yo'q | Qidiruv |

---

### 9.2. Bitta foydalanuvchi

```
GET /appstore/admin/users/{user_id}
```

---

### 9.3. Foydalanuvchi yaratish

```
POST /appstore/admin/users
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| username | string | Ha | |
| email | string | Ha | |
| password | string | Ha | |
| displayName | string | Ha | |
| role | string | Ha | `admin` yoki `publisher` |

**Xatoliklar:** `409` — Username yoki email band

---

### 9.4. Foydalanuvchi yangilash

```
PUT /appstore/admin/users/{user_id}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| displayName | string | Yo'q | |
| email | string | Yo'q | |
| role | string | Yo'q | |
| password | string | Yo'q | |

---

### 9.5. Foydalanuvchi o'chirish

```
DELETE /appstore/admin/users/{user_id}
```

O'zini o'chira olmaydi.

---

## 10. Admin — Dashboard

```
GET /appstore/admin/dashboard
```

`admin` roli uchun to'liq tizim statistikasi, `publisher` roli uchun faqat o'z ilovalari.

---

## 11. Yuklash (Upload)

```
POST /appstore/upload/icon     — Ikonka (max 512KB)
POST /appstore/upload/screenshot — Skrinshot (max 2MB)
POST /appstore/upload/apk      — APK (max 500MB)
POST /appstore/upload/avatar   — Avatar (max 512KB)
```

Har biri `file` form-data qabul qiladi. JWT auth talab qilinadi.

---

## 12. Admin — Ma'lumotlar Eksport/Import

### 12.1. Eksport (ZIP)

```
GET /appstore/admin/data/export
```

| Ruxsat: faqat admin ||

AppStore'dagi barcha ma'lumotlarni va fayllarni ZIP arxiv sifatida yuklab olish.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Ma'lumotlar muvaffaqiyatli eksport qilindi",
    "download_url": "/appstore/exports/data_export.zip",
    "filename": "data_export.zip"
  }
}
```

---

### 12.2. Import (ZIP)

```
POST /appstore/admin/data/import
```

| Ruxsat: faqat admin ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| file | file | Ha | `.zip` arxiv |

Joriy ma'lumotlarni ZIP arxiv bilan almashtiradi.

---

### 12.3. Tozalash (Reset)

```
POST /appstore/admin/data/clear
```

| Ruxsat: faqat admin ||

Barcha AppStore ma'lumotlarini o'chirib, faqat admin foydalanuvchini qayta tiklaydi (`admin`/`admin123`).

---

## 13. Health Check

```
GET /appstore/health
```

---

## AppStore ilova obyekti namunasi

```json
{
  "id": "app-abc123",
  "name": "MXAgent",
  "developer": "MX Soft",
  "shortDescription": "Agentlar uchun mobil ilova",
  "description": "To'liq tavsif...",
  "category": "business",
  "tags": ["agent", "sales", "crm"],
  "icon": "/appstore/uploads/icons/app-abc123.png",
  "screenshots": [
    "/appstore/uploads/screenshots/app-abc123-1.png",
    "/appstore/uploads/screenshots/app-abc123-2.png"
  ],
  "published": true,
  "featured": false,
  "createdBy": "user-admin-001",
  "createdAt": "2024-01-01",
  "updatedAt": "2024-06-01"
}
```

## AppStore versiya obyekti namunasi

```json
{
  "version": "1.2.3",
  "fileSize": 25165824,
  "minAndroid": "8.0",
  "changelog": "Xatoliklar tuzatildi",
  "filePath": "apps/app-abc123/1.2.3.apk",
  "createdAt": "2024-06-01"
}
```
