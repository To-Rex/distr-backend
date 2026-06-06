# MX-Soft Distr — Asosiy API Dokumentatsiyasi

**Base URL:** `http://<host>:8002/api/v1`

**Auth turi:** JWT Bearer Token (`Authorization: Bearer <token>`) yoki legacy token (`Authorization: Bearer <access_token>`)

---

## 1. Autentifikatsiya (`/api/v1/authentication`)

### 1.1. Ro'yxatdan o'tish

```
POST /api/v1/authentication/register
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| username | string | Ha | Login nomi |
| password | string | Ha | Parol |
| email | string | Yo'q | Email |
| first_name | string | Yo'q | Ism |
| last_name | string | Yo'q | Familiya |
| phone_number | string | Yo'q | Telefon |
| photo | string | Yo'q | Rasm URL |
| user_type | enum | Yo'q | Foydalanuvchi turi |
| user_status | enum | Yo'q | Holati |
| company_id | int | Yo'q | Kompaniya ID |
| branch_id | int | Yo'q | Filial ID |
| manager_id | int | Yo'q | Menejer ID |

**Response (201):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "user_type": "ADMIN",
  "created_at": "2024-01-01T00:00:00"
}
```

**Xatoliklar:** `400` — Username already exists | `500` — Server error

---

### 1.2. Login (Legacy token)

```
POST /api/v1/authentication/login-legacy
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| email | string | Ha | Login/username |
| password | string | Ha | Parol |
| device_id | string | Yo'q | Qurilma UUID |
| firebase_token | string | Yo'q | Firebase FCM token |

**Response (200):**
```json
{
  "id": 1,
  "access_token": "abc123...",
  "expires_in": "2024-02-01T00:00:00",
  "user_id": 1,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null
}
```

**Xatoliklar:** `401` — Incorrect username or password | `400` — Account is not active

---

### 1.3. Login (JWT token)

```
POST /api/v1/authentication/login
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| email | string | Ha | Login/username |
| password | string | Ha | Parol |
| device_id | string | Yo'q | Qurilma UUID |
| firebase_token | string | Yo'q | Firebase FCM token |

**Response (200):**
```json
{
  "id": 1,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": "2024-02-01T00:00:00",
  "user_id": 1,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": null
}
```

**Xatoliklar:** `401` — Incorrect username or password | `400` — Account is not active

---

### 1.4. Token yangilash

```
POST /api/v1/authentication/refresh-token
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| refresh_token | string | Ha | Refresh token |

**Response (200):** `JwtTokenResponse` (yangi juftlik access + refresh token)

**Xatoliklar:** `401` — Invalid or expired refresh token

---

### 1.5. Profil

```
GET /api/v1/authentication/profile
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Header** ||||
| Authorization | Bearer `<token>` | Ha | JWT token |

**Response (200):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": null,
  "phone_number": null,
  "photo": null,
  "user_type": "ADMIN",
  "company_id": null,
  "branch_id": null,
  "company_rel": null,
  "branch_rel": null,
  "manager": null,
  "manager_id": null,
  "user_1c_id": null,
  "user_1c_login": null,
  "user_1c_password": null,
  "created_at": "2024-01-01T00:00:00",
  "user_status": "ACTIVE"
}
```

---

### 1.6. Logout

```
GET /api/v1/authentication/logout
```

Hech qanday body yoki parametr talab qilinmaydi. Har doim 200 qaytaradi.

---

## 2. Foydalanuvchi Boshqaruvi (`/api/v1/user-manager`)

**Ruxsat:** ADMIN, MANAGER, SUPERADMIN, CEO

### 2.1. Foydalanuvchilar ro'yxati

```
GET /api/v1/user-manager
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| user_type | enum | Yo'q | Filtrlash (SUPERADMIN, ADMIN, MANAGER, AGENT...) |
| **Header** ||||
| Authorization | Bearer `<token>` | Ha | JWT token |

**Response (200):** `List[UserResponse]`

---

### 2.2. Bitta foydalanuvchi

```
GET /api/v1/user-manager/{user_id}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Path** ||||
| user_id | int | Ha | Foydalanuvchi ID |

**Response (200):** `UserResponse`

**Xatoliklar:** `404` — User not found | `403` — Insufficient permissions

---

### 2.3. Foydalanuvchi yaratish

```
POST /api/v1/user-manager/create
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| username | string | Ha | Login |
| password | string | Ha | Parol |
| email | string | Yo'q | Email |
| first_name | string | Yo'q | Ism |
| last_name | string | Yo'q | Familiya |
| phone_number | string | Yo'q | Telefon |
| user_type | enum | Yo'q | Foydalanuvchi turi |
| user_status | enum | Yo'q | Holati |
| company_id | int | Yo'q | Kompaniya ID |
| branch_id | int | Yo'q | Filial ID |
| manager_id | int | Yo'q | Menejer ID |
| user_1c_id | int | Yo'q | 1C tizim ID |
| user_1c_login | string | Yo'q | 1C login |
| user_1c_password | string | Yo'q | 1C parol |

**Response (201):** `UserResponse`

**Xatoliklar:** `400` — Username or email already exists

---

### 2.4. Foydalanuvchi yangilash

```
PATCH /api/v1/user-manager/{user_id}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Path** ||||
| user_id | int | Ha | Foydalanuvchi ID |
| **Body (JSON)** ||||
| username | string | Yo'q | Yangi username |
| password | string | Yo'q | Yangi parol |
| email | string | Yo'q | Yangi email |
| ... (boshqa UserUpdate maydonlari) ||||

**Response (200):** `UserResponse`

**Xatoliklar:** `404` — User not found | `403` — Insufficient permissions

---

### 2.5. Foydalanuvchi o'chirish

```
DELETE /api/v1/user-manager/{user_id}
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Path** ||||
| user_id | int | Ha | Foydalanuvchi ID |

**Response:** `204 No Content`

**Xatoliklar:** `404` — User not found | `400` — Cannot delete your own account | `403` — Insufficient permissions

---

## 3. Kompaniyalar (`/api/v1/companies`)

### 3.1. Kompaniya yaratish

```
POST /api/v1/companies/
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| name | string (max 255) | Ha | Kompaniya nomi |
| inn | string (max 50) | Yo'q | INN raqami |
| base_url | string (max 500) | Yo'q | Kompaniya asosiy URL |
| asl_belgi_token | string (max 500) | Yo'q | ASL belgi tokeni |

**Response (201):**
```json
{
  "id": 1,
  "name": "My Company",
  "inn": null,
  "base_url": "",
  "asl_belgi_token": "",
  "created_at": "2024-01-01T00:00:00"
}
```

**Xatoliklar:** `400` — Company with this name already exists | `403` — Not enough permissions

---

### 3.2. Kompaniyalar ro'yxati

```
GET /api/v1/companies/
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| skip | int | Yo'q (0) | Offset |
| limit | int | Yo'q (100) | Limit |

**Response (200):** `List[CompanyWithBranchesResponse]` — Har bir kompaniya o'z filiallari bilan

---

### 3.3. Bitta kompaniya

```
GET /api/v1/companies/{company_id}
```

**Response (200):** `CompanyWithBranchesResponse`

**Xatoliklar:** `404` — Company not found

---

### 3.4. Kompaniya yangilash

```
PUT /api/v1/companies/{company_id}
```

| Ruxsat: SUPERADMIN, ADMIN ||

**Response (200):** `CompanyResponse`

**Xatoliklar:** `404` — Company not found | `403` — Not enough permissions

---

### 3.5. Kompaniya o'chirish

```
DELETE /api/v1/companies/{company_id}
```

| Ruxsat: faqat SUPERADMIN ||

**Response:** `204 No Content`

**Xatoliklar:** `404` — Company not found | `403` — Only superadmin can delete

---

## 4. Security Key (`/api/v1/companies`)

### 4.1. Security kalit yaratish

```
POST /api/v1/companies/{company_id}/security-keys
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Path** ||||
| company_id | int | Ha | Kompaniya ID |
| **Body (JSON)** ||||
| key | string (max 255) | Ha | Kalit qiymati |
| company_id | int | Ha | Kompaniya ID (path bilan mos kelishi kerak) |

**Response (201):**
```json
{
  "id": 1,
  "key": "my-secret-key",
  "company_id": 1
}
```

---

### 4.2. Kompaniya security kalitlari ro'yxati

```
GET /api/v1/companies/{company_id}/security-keys
```

**Response (200):** `List[SecurityKeyResponse]`

---

### 4.3. Bitta security kalit

```
GET /api/v1/companies/security-keys/{key_id}
```

**Xatoliklar:** `404` — Security key not found

---

### 4.4. Security kalit yangilash

```
PUT /api/v1/companies/security-keys/{key_id}
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| key | string (max 255) | Yo'q | Yangi kalit qiymati |

---

### 4.5. Security kalit o'chirish

```
DELETE /api/v1/companies/security-keys/{key_id}
```

| Ruxsat: faqat SUPERADMIN ||

**Response:** `204 No Content`

---

## 5. Filiallar (`/api/v1/branches`)

### 5.1. Filial yaratish

```
POST /api/v1/branches/
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| name | string | Ha | Filial nomi |
| company_id | int | Yo'q | Kompaniya ID |

**Response (201):**
```json
{
  "id": 1,
  "name": "Toshkent filiali",
  "company_id": 1,
  "created_at": "2024-01-01T00:00:00"
}
```

---

### 5.2. Filiallar ro'yxati

```
GET /api/v1/branches/
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| skip | int | Yo'q (0) | Offset |
| limit | int | Yo'q (100) | Limit |

**Response (200):** `List[BranchResponse]`

---

### 5.3. Bitta filial

```
GET /api/v1/branches/{branch_id}
```

**Xatoliklar:** `404` — Branch not found

---

### 5.4. Filial yangilash

```
PUT /api/v1/branches/{branch_id}
```

| Ruxsat: SUPERADMIN, ADMIN ||

**Response (200):** `BranchResponse`

---

### 5.5. Filial o'chirish

```
DELETE /api/v1/branches/{branch_id}
```

| Ruxsat: faqat SUPERADMIN ||

**Response:** `204 No Content`

---

## 6. Qurilmalar (`/api/v1/devices`)

### 6.1. Qurilma yaratish

```
POST /api/v1/devices/
```

| Ruxsat: SUPERADMIN, ADMIN, MANAGER ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| name | string (max 100) | Ha | Qurilma nomi |
| device_uuid | string (max 255) | Ha | Unique UUID |
| platform | string (max 50) | Yo'q | Platforma (Android/iOS) |
| model | string (max 100) | Yo'q | Model |
| os_version | string (max 50) | Yo'q | OS versiyasi |
| app_version | string (max 50) | Yo'q | Ilova versiyasi |
| is_active | bool | Yo'q (True) | Faollik |
| user_id | int | Yo'q | Foydalanuvchi ID |

**Response (201):**
```json
{
  "id": 1,
  "name": "Samsung A52",
  "device_uuid": "abc-123-def",
  "platform": "Android",
  "model": "SM-A525F",
  "os_version": "13",
  "app_version": "1.0.0",
  "is_active": true,
  "last_seen": null,
  "user_id": 1,
  "created_at": "2024-01-01T00:00:00"
}
```

**Xatoliklar:** `400` — Device UUID already exists | `404` — User not found

---

### 6.2. Qurilmalar ro'yxati

```
GET /api/v1/devices/
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| is_active | bool | Yo'q | Faollik bo'yicha filtrlash |
| user_id | int | Yo'q | Foydalanuvchi bo'yicha filtrlash |
| skip | int | Yo'q (0) | Offset |
| limit | int | Yo'q (100) | Limit |

**Response (200):** `List[DeviceResponse]`

---

### 6.3. Bitta qurilma

```
GET /api/v1/devices/{device_id}
```

**Xatoliklar:** `404` — Device not found

---

### 6.4. Qurilma yangilash

```
PUT /api/v1/devices/{device_id}
```

| Ruxsat: SUPERADMIN, ADMIN, MANAGER ||

**Response (200):** `DeviceResponse`

---

### 6.5. Qurilma o'chirish

```
DELETE /api/v1/devices/{device_id}
```

| Ruxsat: faqat SUPERADMIN ||

**Response:** `204 No Content`

---

## 7. Joylashuvlar (`/api/v1/locations`)

### 7.1. Joylashuv yaratish

```
POST /api/v1/locations/
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| latitude | float (−90..90) | Ha | Kenglik |
| longitude | float (−180..180) | Ha | Uzunlik |
| device_name | string (max 100) | Yo'q | Qurilma nomi |
| is_active | bool | Yo'q (True) | Faollik |
| user_id | int | Ha | Foydalanuvchi ID |

**Response (201):**
```json
{
  "id": 1,
  "latitude": 41.2995,
  "longitude": 69.2401,
  "device_name": "Samsung A52",
  "is_active": true,
  "user_id": 1,
  "created_at": "2024-01-01T12:00:00"
}
```

**Xatoliklar:** `404` — User not found

---

### 7.2. Barcha joylashuvlar

```
GET /api/v1/locations/
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| is_active | bool | Yo'q | Faollik bo'yicha filtrlash |
| user_id | int | Yo'q | Foydalanuvchi bo'yicha filtrlash |

**Response (200):** `List[LocationRead]`

---

### 7.3. Bitta joylashuv

```
GET /api/v1/locations/{location_id}
```

**Xatoliklar:** `404` — Location not found

---

### 7.4. Joylashuv yangilash

```
PUT /api/v1/locations/{location_id}
```

**Response (200):** `LocationRead`

---

### 7.5. Joylashuv o'chirish

```
DELETE /api/v1/locations/{location_id}
```

**Response:** `204 No Content`

---

### 7.6. Kunlik tarix

```
GET /api/v1/locations/user-history/{user_id}
```

Bugungi kun davomida foydalanuvchining barcha joylashuv tarixini qaytaradi.

**Response (200):** `List[LocationRead]`

**Xatoliklar:** `404` — User not found

---

### 7.7. WebSocket — Real-time joylashuv

```
WS /api/v1/locations/ws/admvs?token=<JWT_TOKEN>
```

**Auth:** Query parametrda JWT token

**Yuboriladigan format:**
```json
{
  "action": "update_location",
  "latitude": 41.2995,
  "longitude": 69.2401,
  "device_name": "Samsung A52",
  "accuracy": 10.0,
  "speed": 5.0
}
```

**Serverdan keladigan:** `{"action": "ping"}` — 30 soniyalik heartbeat

**Uzilganda:** Avtomatik disconnect, qayta ulanish kerak.

---

## 8. Ilova va Versiyalar (`/api/v1/apps`)

### 8.1. Ilova yaratish

```
POST /api/v1/apps/
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| name | string | Ha | Ilova nomi |
| tag | string | Yo'q | Teg |

**Response (201):**
```json
{
  "id": 1,
  "name": "MXAgent",
  "tag": null,
  "created_at": "2024-01-01T00:00:00"
}
```

**Xatoliklar:** `400` — App with this name already exists

---

### 8.2. Ilovalar ro'yxati

```
GET /api/v1/apps/
```

**Response (200):** `List[AppResponse]`

---

### 8.3. Eng so'nggi versiya

```
GET /api/v1/apps/latest-version?app_type=agent
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| app_type | string | Ha | Ilova turi (masalan `agent`, `deliverer`) |

**Response (200):**
```json
{
  "id": 1,
  "version": "1.2.3",
  "build_number": 10,
  "force_update": false,
  "update_url": "/static/uploads/apps/mxagent.apk",
  "message": "Yangi funksiyalar qo'shildi",
  "title": "MXAgent v1.2.3",
  "app_id": 1,
  "created_at": "2024-01-01T00:00:00"
}
```

**Xatoliklar:** `404` — App type not found / No version found

---

### 8.4. Bitta ilova

```
GET /api/v1/apps/{app_id}
```

**Xatoliklar:** `404` — App not found

---

### 8.5. Ilova yangilash

```
PUT /api/v1/apps/{app_id}
```

| Ruxsat: SUPERADMIN, ADMIN ||

**Response (200):** `AppResponse`

---

### 8.6. Ilova o'chirish

```
DELETE /api/v1/apps/{app_id}
```

| Ruxsat: faqat SUPERADMIN ||

**Response:** `204 No Content`

---

### 8.7. Versiya yaratish

```
POST /api/v1/apps/{app_id}/versions
```

| Ruxsat: SUPERADMIN, ADMIN ||

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Body (JSON)** ||||
| version | string | Ha | Versiya raqami |
| build_number | int | Ha | Build raqami |
| force_update | bool | Yo'q (false) | Majburiy yangilanish |
| update_url | string | Yo'q | Yuklab olish URL |
| message | string | Yo'q | Xabar |
| title | string | Yo'q | Sarlavha |
| app_id | int | Ha | Ilova ID (path bilan mos) |

**Response (201):** `VersionResponse`

---

### 8.8. Ilova versiyalari ro'yxati

```
GET /api/v1/apps/{app_id}/versions
```

**Response (200):** `List[VersionResponse]` — Yangidan eskiga tartiblangan

---

### 8.9. Bitta versiya

```
GET /api/v1/apps/versions/{version_id}
```

**Xatoliklar:** `404` — Version not found

---

### 8.10. Versiya yangilash

```
PUT /api/v1/apps/versions/{version_id}
```

| Ruxsat: SUPERADMIN, ADMIN ||

**Response (200):** `VersionResponse`

---

### 8.11. Versiya o'chirish

```
DELETE /api/v1/apps/versions/{version_id}
```

| Ruxsat: faqat SUPERADMIN ||

**Response:** `204 No Content`

---

### 8.12. APK fayl yuklash

```
POST /api/v1/apps/upload-apk
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Form Data** ||||
| file | file | Ha | `.apk`, `.ipa` yoki `.exe` fayl |

**Qabul qilinadigan formatlar:** `.apk`, `.ipa`, `.exe`

**Response (200):**
```json
{
  "filename": "mxagent.apk",
  "url": "/static/uploads/apps/mxagent.apk",
  "size": 52428800
}
```

**Xatoliklar:** `400` — Not allowed format | `409` — File already exists

---

## UserType (Foydalanuvchi turlari)

| Qiymat | Tavsif |
|--------|--------|
| `USER` | Oddiy foydalanuvchi |
| `SUPERADMIN` | Bosh admin |
| `ADMIN` | Admin |
| `MANAGER` | Menejer |
| `SUPERVISOR` | Nazoratchi |
| `AGENT` | Sotuv agenti |
| `DELIVERER` | Yetkazib beruvchi |
| `VENDOR_AGENT` | Yetkazib beruvchi agenti |
| `CLIENT` | Mijoz |
| `DEALER` | Diler |
| `FACTORY` | Zavod |
| `CEO` | Rahbar |
| `FINANCIST` | Moliya xodimi |
| `WAREHOUSE` | Ombor xodimi |
| `SALESMAN` | Sotuvchi |
| `CASHIER` | Kassir |
| `HR` | Kadrlar bo'limi |
| `MARKETING` | Marketing xodimi |
| `EXTERNAL_SELLER` | Tashqi sotuvchi |
| `MERCHANDISER` | Merchandayser |

## UserStatus (Foydalanuvchi holati)

| Qiymat | Tavsif |
|--------|--------|
| `ACTIVE` | Faol |
| `INACTIVE` | Faol emas |
| `PENDING` | Kutmoqda |
| `BLOCKED` | Bloklangan |
