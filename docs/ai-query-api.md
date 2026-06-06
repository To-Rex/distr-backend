# MX-Soft Distr — AI Query API

**Base URL:** `http://<host>:8002/api/v1/ai-query`

Tabiiy tilda berilgan savollarni PostgreSQL SQL so'rovga aylantirib, javob qaytaradi. **Groq AI** (LLaMA 3.3 70B) ishlatiladi.

---

## AI So'rov

```
POST /api/v1/ai-query
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Header** ||||
| Authorization | Bearer `<token>` | Ha | JWT token |
| **Body (JSON)** ||||
| question | string | Ha | Savol (o'zbek, rus yoki ingliz tilida) |

**Response (200):**
```json
{
  "sql": "SELECT u.username, COUNT(ws.id) as session_count FROM users u JOIN working_sessions ws ON u.id = ws.user_id WHERE u.user_type = 'AGENT' GROUP BY u.id, u.username ORDER BY session_count DESC LIMIT 10",
  "answer": "Eng faol 10 ta agent: Ali (45 sessiya), Vali (38 sessiya)... - MX Soft Agent",
  "formatted": "**Eng faol agentlar:**\n\n| Agent | Sessiyalar soni |\n|-------|----------------|\n| Ali | 45 |\n| Vali | 38 |\n...\n\n- MX Soft Agent",
  "format": "markdown",
  "count": 10,
  "data": [
    {"username": "agent1", "session_count": 45},
    {"username": "agent2", "session_count": 38}
  ]
}
```

| Maydon | Tavsif |
|--------|--------|
| sql | Yaratilgan SQL so'rov |
| answer | Oddiy matn javob |
| formatted | Markdown formatda javob (jadval, ro'yxat) |
| format | Har doim `markdown` |
| count | Natijalar soni |
| data | SQL dan olingan xom ma'lumot (barcha qatorlar) |

**Xatoliklar:**
- `400` — Only SELECT queries are allowed / Query error
- `500` — GROQ_API_KEY not configured
- `502` — AI service error

---

## Qanday ishlaydi

1. **Klassifikatsiya:** Savol `data` yoki `general` kategoriyaga ajratiladi
2. **General** savollar: Chat javob qaytariladi (SQL ishlatilmaydi) — `"sql": null`
3. **Data** savollar: Savol → SQL → PostgreSQL → Natija → Markdown javob

## Qo'llab-quvvatlanadigan jadvallar

| Jadval | Izoh |
|--------|------|
| `users` | Barcha foydalanuvchilar |
| `companies` | Kompaniyalar |
| `security_keys` | Security kalitlar |
| `locations` | GPS joylashuv tarixi |
| `devices` | Mobil qurilmalar |
| `apps` | Ilovalar |
| `app_versions` | Ilova versiyalari |
| `working_sessions` | Ish sessiyalari |
| `notifications` | Bildirishnomalar |
| `notification_user_status` | Bildirishnoma holati |
| `access_tokens` | Tokenlar |

## Misol savollar

- "Eng faol agentlar kimlar?" → `working_sessions` da COUNT, users bilan JOIN
- "Nechta kompaniya bor?" → `SELECT COUNT(*) FROM companies`
- "Bugungi bildirishnomalar ro'yxati" → `notifications` WHERE created_at >= CURRENT_DATE
- "Toshkentdagi agentlar" → users + locations orqali
- "Eng ko'p qurilmaga ega foydalanuvchi" → devices jadvalidan

## Xavfsizlik

- Faqat `SELECT` va `WITH` so'rovlar ruxsat etilgan
- INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, EXEC va boshqalar **bloklangan**
- Javob 100 ta qatorgacha LIMIT qo'yiladi
