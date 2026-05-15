# AppStore API

Ilovalar do'koni uchun to'liq API. Ilovalarni ro'yxatdan o'tkazish, boshqarish, yuklab olish va foydalanuvchilarni boshqarish imkoniyatlarini taqdim etadi.

**Base URL:** `/appstore`

---

## Sog'likni tekshirish

```
GET /appstore/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "appstore"
}
```

---

## Autentifikatsiya

### Tizimga kirish

```
POST /appstore/auth/login
```

**Request body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "jwt...",
    "user": {
      "id": "uuid",
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "displayName": "Admin",
      "avatar": "/appstore/uploads/avatars/uuid.ext",
      "createdAt": "2026-01-01T00:00:00"
    }
  }
}
```

`refreshToken` httpOnly cookie o'rnatiladi (7 kun).

| Maydon | Turi | Tavsif |
|---|---|---|
| `username` | `string` | Foydalanuvchi nomi |
| `password` | `string` | Parol |

---

### Tizimdan chiqish

```
POST /appstore/auth/logout
```

**Header:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "message": "Muvaffaqiyatli chiqildi"
}
```

`refreshToken` cookie o'chiriladi.

---

### Profilni olish

```
GET /appstore/auth/me
```

**Header:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "displayName": "Admin",
    "avatar": "/appstore/uploads/avatars/uuid.ext",
    "createdAt": "2026-01-01T00:00:00"
  }
}
```

---

### Profilni yangilash

```
PUT /appstore/auth/profile
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data`

| Maydon | Turi | Tavsif |
|---|---|---|
| `displayName` | `string` | Ko'rinadigan nom |
| `avatar` | `file` | Avatar rasm (max 512KB) |

**Response:** Profil ma'lumotlari (yuqoridagi kabi)

---

### Parolni o'zgartirish

```
PATCH /appstore/auth/change-password
```

**Header:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "currentPassword": "current123",
  "newPassword": "new123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Parol muvaffaqiyatli o'zgartirildi"
}
```

---

### Tokenni yangilash

```
POST /appstore/auth/refresh
```

`refreshToken` cookie yoki query parametr orqali yuboriladi.

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "new_jwt..."
  }
}
```

---

## Ilovalar (Ommaviy)

### Ilovalar ro'yxati

```
GET /appstore/apps
```

**Query parametrlar:**

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `q` | - | Qidirish matni |
| `category` | - | Kategoriya bo'yicha filtrlash |
| `sort` | `updated` | Saralash: `updated`, `newest`, `downloads`, `name` |
| `page` | `1` | Sahifa |
| `limit` | `20` | Limit |
| `published` | `true` | Nashr qilinganlar |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "My App",
      "icon": "/appstore/uploads/icons/uuid.ext",
      "developer": "Dev Name",
      "shortDescription": "Qisqa tavsif",
      "category": "productivity",
      "tags": ["tool", "utility"],
      "totalDownloads": 150,
      "latestVersion": "1.0.0",
      "hasApk": true,
      "updatedAt": "2026-01-15T12:00:00",
      "createdAt": "2026-01-01T12:00:00",
      "published": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

---

### Tanlangan ilovalar

```
GET /appstore/apps/featured?limit=3
```

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `limit` | `3` | Qaytariladigan ilovalar soni |

**Response:** Ilovalar ro'yxati (yuqoridagi kabi)

---

### So'nggi yangilanganlar

```
GET /appstore/apps/recently-updated?limit=4
```

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `limit` | `4` | Qaytariladigan ilovalar soni |

**Response:** Ilovalar ro'yxati

---

### Eng yangi ilovalar

```
GET /appstore/apps/newest?limit=4
```

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `limit` | `4` | Qaytariladigan ilovalar soni |

**Response:** Ilovalar ro'yxati

---

### Qidirish takliflari

```
GET /appstore/apps/search-suggestions?q=my&limit=5
```

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `q` | - | Qidirish matni (min 2 belgi) |
| `limit` | `5` | Takliflar soni |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "My App",
      "icon": "/appstore/uploads/icons/uuid.ext",
      "category": "productivity",
      "latestVersion": "1.0.0"
    }
  ]
}
```

---

### Ilova tafsilotlari

```
GET /appstore/apps/{app_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "My App",
    "icon": "/appstore/uploads/icons/uuid.ext",
    "developer": "Dev Name",
    "shortDescription": "Qisqa tavsif",
    "description": "To'liq tavsif",
    "category": "productivity",
    "tags": ["tool", "utility"],
    "screenshots": ["/appstore/uploads/screenshots/uuid1.ext"],
    "versions": [
      {
        "version": "1.0.0",
        "releaseDate": "2026-01-15",
        "fileSize": 5242880,
        "minAndroid": "8.0",
        "changelog": "Birinchi versiya",
        "downloadUrl": "/appstore/uploads/apks/uuid.apk",
        "downloadCount": 100,
        "isLatest": true,
        "hasApk": true
      }
    ],
    "hasApk": true,
    "totalDownloads": 150,
    "updatedAt": "2026-01-15T12:00:00",
    "createdAt": "2026-01-01T12:00:00",
    "published": true,
    "createdBy": "uuid"
  }
}
```

---

### Versiyalar ro'yxati

```
GET /appstore/apps/{app_id}/versions
```

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `sort` | `newest` | Saralash: `newest`, `oldest` |
| `page` | `1` | Sahifa |
| `limit` | `20` | Limit |

**Response:** Paginated versiyalar ro'yxati

---

### Versiya tafsilotlari

```
GET /appstore/apps/{app_id}/versions/{version}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "appId": "uuid",
    "appName": "My App",
    "appIcon": "/appstore/uploads/icons/uuid.ext",
    "version": "1.0.0",
    "releaseDate": "2026-01-15",
    "fileSize": 5242880,
    "minAndroid": "8.0",
    "changelog": "Birinchi versiya",
    "downloadUrl": "/appstore/uploads/apks/uuid.apk",
    "downloadCount": 100,
    "isLatest": true,
    "isNewerAvailable": false,
    "latestVersion": "1.0.0"
  }
}
```

---

### APK yuklab olish

```
GET /appstore/apps/{app_id}/versions/{version}/download
```

Agar fayl mavjud bo'lsa, `FileResponse` qaytaradi (`application/vnd.android.package-archive`). Aks holda `downloadUrl` ga redirect qiladi.

---

### Skrinshotlar ro'yxati

```
GET /appstore/apps/{app_id}/screenshots
```

**Response:**
```json
{
  "success": true,
  "data": {
    "appId": "uuid",
    "appName": "My App",
    "screenshots": [
      {
        "id": "uuid",
        "url": "/appstore/uploads/screenshots/uuid.ext",
        "order": 1
      }
    ]
  }
}
```

---

## Kategoriyalar

```
GET /appstore/categories
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "productivity",
      "name": "Productivity",
      "labelUz": "Samaradorlik",
      "appCount": 5
    }
  ]
}
```

Mavjud kategoriyalar: `productivity`, `communication`, `development`, `security`, `media`, `utilities`, `finance`, `education`.

---

## Statistika

```
GET /appstore/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "totalApps": 10,
    "totalVersions": 15,
    "totalDownloads": 1000,
    "totalCategories": 8
  }
}
```

---

## Fayl yuklash

Barcha yuklashlar `multipart/form-data` formatida `file` maydoni bilan yuboriladi.

### Ikonka yuklash

```
POST /appstore/upload/icon
```

**Header:** `Authorization: Bearer <token>`

| Maydon | Chegara |
|---|---|
| file | 512KB |

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "/appstore/uploads/icons/uuid.ext"
  }
}
```

---

### Skrinshot yuklash

```
POST /appstore/upload/screenshot
```

**Header:** `Authorization: Bearer <token>`

| Maydon | Chegara |
|---|---|
| file | 2MB |

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "/appstore/uploads/screenshots/uuid.ext"
  }
}
```

---

### APK yuklash

```
POST /appstore/upload/apk
```

**Header:** `Authorization: Bearer <token>`

| Maydon | Chegara |
|---|---|
| file | 500MB |

**Response:**
```json
{
  "success": true,
  "data": {
    "filePath": "/appstore/uploads/apks/uuid.apk",
    "fileSize": 5242880,
    "versionName": "1.0.0",
    "packageName": "com.example.app",
    "minSdkVersion": "26"
  }
}
```

---

### Avatar yuklash

```
POST /appstore/upload/avatar
```

**Header:** `Authorization: Bearer <token>`

| Maydon | Chegara |
|---|---|
| file | 512KB |

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "/appstore/uploads/avatars/uuid.ext"
  }
}
```

---

## Admin: Dashboard

```
GET /appstore/admin/dashboard
```

**Header:** `Authorization: Bearer <token>`

**Response (Admin):**
```json
{
  "success": true,
  "data": {
    "totalApps": 10,
    "publishedApps": 8,
    "draftApps": 2,
    "totalDownloads": 1000,
    "totalUsers": 20,
    "totalPublishers": 3,
    "recentApps": [
      {
        "id": "uuid",
        "name": "My App",
        "version": "1.0.0",
        "status": "published",
        "createdAt": "2026-01-15T12:00:00"
      }
    ],
    "appsByCategory": [
      { "name": "Samaradorlik", "value": 5 }
    ],
    "topAppsByDownloads": [
      { "name": "My App", "downloads": 500 }
    ]
  }
}
```

**Response (Publisher):** Publisher uchun faqat o'z ilovalari bo'yicha ma'lumotlar (`totalUsers` va `totalPublishers` bo'lmaydi).

---

## Admin: Ilovalar

### Ilovalar ro'yxati (Admin)

```
GET /appstore/admin/apps
```

**Header:** `Authorization: Bearer <token>`

Admin barcha ilovalarni, publisher faqat o'z ilovalarini ko'radi.

**Response:** Paginated ilovalar ro'yxati (ommaviy ko'rinishdagi kabi, qo'shimcha maydonlar bilan)

---

### Ilova tafsilotlari (Admin)

```
GET /appstore/admin/apps/{app_id}
```

**Header:** `Authorization: Bearer <token>`

**Response:** To'liq ilova ma'lumotlari + `creatorName`

---

### Ilova yaratish

```
POST /appstore/admin/apps
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data`

| Maydon | Turi | Talab | Tavsif |
|---|---|---|---|
| `name` | `string` | Ha | Ilova nomi |
| `shortDescription` | `string` | Ha | Qisqa tavsif |
| `category` | `string` | Ha | Kategoriya |
| `developer` | `string` | Yo'q | Dasturchi |
| `description` | `string` | Yo'q | To'liq tavsif |
| `tags` | `string` | Yo'q | Teglar (vergul bilan ajratilgan) |
| `published` | `string` | Yo'q | `"true"` yoki `"false"` |
| `icon` | `file` | Yo'q | Ilova ikonkasi |

---

### Ilovani yangilash

```
PUT /appstore/admin/apps/{app_id}
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data` (yaratish bilan bir xil maydonlar)

---

### Ilovani o'chirish

```
DELETE /appstore/admin/apps/{app_id}
```

**Header:** `Authorization: Bearer <token>`

---

### Nashr holatini o'zgartirish

```
PATCH /appstore/admin/apps/{app_id}/toggle-publish
```

**Header:** `Authorization: Bearer <token>`

---

## Admin: Versiyalar

### Versiya yaratish

```
POST /appstore/admin/apps/{app_id}/versions
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data`

| Maydon | Turi | Talab | Tavsif |
|---|---|---|---|
| `version` | `string` | Ha | Versiya raqami |
| `file` | `file` | Ha | APK fayl |
| `minAndroid` | `string` | Yo'q | Minimal Android versiyasi (birlamchi: `8.0`) |
| `changelog` | `string` | Yo'q | O'zgarishlar tarixi |

---

### Versiyani yangilash

```
PUT /appstore/admin/apps/{app_id}/versions/{version}
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data`

| Maydon | Turi | Tavsif |
|---|---|---|
| `changelog` | `string` | O'zgarishlar tarixi |
| `minAndroid` | `string` | Minimal Android versiyasi |
| `file` | `file` | Yangi APK (ixtiyoriy) |

---

### Versiyani o'chirish

```
DELETE /appstore/admin/apps/{app_id}/versions/{version}
```

**Header:** `Authorization: Bearer <token>`

---

## Admin: Skrinshotlar

### Skrinshot yuklash

```
POST /appstore/admin/apps/{app_id}/screenshots
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data` - `screenshots` maydoni (bir yoki bir nechta fayl)

---

### Skrinshot o'chirish

```
DELETE /appstore/admin/apps/{app_id}/screenshots/{index}
```

**Header:** `Authorization: Bearer <token>`

---

## Admin: Foydalanuvchilar (Admin only)

### Foydalanuvchilar ro'yxati

```
GET /appstore/admin/users
```

**Header:** `Authorization: Bearer <token>`

| Parametr | Tavsif |
|---|---|
| `q` | Qidirish matni |

---

### Foydalanuvchi tafsilotlari

```
GET /appstore/admin/users/{user_id}
```

**Header:** `Authorization: Bearer <token>`

---

### Foydalanuvchi yaratish

```
POST /appstore/admin/users
```

**Header:** `Authorization: Bearer <token>`

**Request body:**
```json
{
  "username": "publisher1",
  "email": "pub@example.com",
  "password": "secret123",
  "displayName": "Publisher One",
  "role": "publisher"
}
```

| Maydon | Turi | Talab | Tavsif |
|---|---|---|---|
| `username` | `string` | Ha | Foydalanuvchi nomi |
| `email` | `string` | Ha | Email |
| `password` | `string` | Ha | Parol |
| `displayName` | `string` | Yo'q | Ko'rinadigan nom |
| `role` | `string` | Ha | Rol: `admin` yoki `publisher` |

---

### Foydalanuvchini yangilash

```
PUT /appstore/admin/users/{user_id}
```

**Header:** `Authorization: Bearer <token>`

**Request body:** Ixtiyoriy maydonlar: `displayName`, `email`, `role`, `password`

---

### Foydalanuvchini o'chirish

```
DELETE /appstore/admin/users/{user_id}
```

**Header:** `Authorization: Bearer <token>`

---

## Admin: Ma'lumotlarni eksport/import

### Eksport

```
GET /appstore/admin/data/export
```

**Header:** `Authorization: Bearer <token>`

Barcha ma'lumotlarni ZIP arxivga eksport qiladi.

**Response:**
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

### Import

```
POST /appstore/admin/data/import
```

**Header:** `Authorization: Bearer <token>`

**Request:** `multipart/form-data` - `file` (ZIP fayl)

Mavjud ma'lumotlarni yuklangan ZIP bilan almashtiradi.

---

### Tozalash

```
POST /appstore/admin/data/clear
```

**Header:** `Authorization: Bearer <token>`

Barcha ma'lumotlarni o'chirib, boshlang'ich holatga qaytaradi (`admin/admin123` admin foydalanuvchisi qayta yaratiladi).

---

## Autentifikatsiya turlari

| Tur | Usul |
|---|---|
| JWT Token | `Authorization: Bearer <token>` header |
| Refresh Token | httpOnly cookie yoki query parametr |
| Rol tekshiruvi | `require_admin` middleware (Admin huquq talab qiladigan endpointlar) |

## Ma'lumotlar saqlash

Ma'lumotlar JSON fayllarda saqlanadi (`apps/app_store/data/`):

| Fayl | Tavsif |
|---|---|
| `users.json` | Foydalanuvchilar |
| `apps.json` | Ilovalar |
| `versions.json` | Versiyalar |

Yuklangan fayllar: `uploads/icons/`, `uploads/screenshots/`, `uploads/apks/`, `uploads/avatars/`
