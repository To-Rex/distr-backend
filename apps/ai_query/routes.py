import os
import re
from httpx import AsyncClient
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_async_session
from apps.base.models import Base
from apps.user.models import User, UserType, UserStatus
from apps.user.di import get_current_user_by_token

import apps.company.models  # noqa: F401
import apps.location.models  # noqa: F401
import apps.device.models  # noqa: F401
import apps.app_version.models  # noqa: F401
import apps.working_session_tracking.models  # noqa: F401
import apps.notification.models  # noqa: F401
import apps.alembic_version.models  # noqa: F401

router = APIRouter(
    prefix="/ai-query",
    tags=["AI Query"],
)


def _get_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GROQ_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1]
    except FileNotFoundError:
        pass
    return ""


GROQ_API_KEY = _get_api_key()
GROQ_MODEL = "llama-3.3-70b-versatile"


class AIQueryRequest(BaseModel):
    question: str


TABLE_META = {
    "users": {
        "label": "Foydalanuvchilar / Users",
        "desc": "Tizimdagi barcha foydalanuvchilar: xodimlar, adminlar, agentlar, menejerlar va boshqalar. This is the main table for any user-related query.",
    },
    "companies": {
        "label": "Kompaniyalar / Companies",
        "desc": "Tizimda ro'yxatdan o'tgan kompaniyalar va tashkilotlar.",
    },
    "security_keys": {
        "label": "Security Keys",
        "desc": "Har bir kompaniyaga tegishli maxfiy kalit (one-to-one companies bilan).",
    },
    "locations": {
        "label": "Joylashuvlar / Locations",
        "desc": "Foydalanuvchilarning GPS joylashuv tarixi (kenglik, uzunlik). Real-time WebSocket orqali yangilanadi.",
    },
    "devices": {
        "label": "Qurilmalar / Devices",
        "desc": "Foydalanuvchilarning mobil qurilmalari (platforma, model, OS versiyasi).",
    },
    "apps": {
        "label": "Ilovalar / Apps",
        "desc": "Tizimdagi ilovalar ro'yxati (masalan: MXTrade, MXSoft).",
    },
    "app_versions": {
        "label": "Ilova versiyalari / App Versions",
        "desc": "Ilovalarning versiyalari, build raqamlari, majburiy yangilanish ma'lumotlari.",
    },
    "working_sessions": {
        "label": "Ish sessiyalari / Working Sessions",
        "desc": "Xodimlarning ilova ishlatish sessiyalari. 'Faollik/aktivlik' ma'nosi shu jadvalda. Each row = one launch/app open session.",
    },
    "notifications": {
        "label": "Bildirishnomalar / Notifications",
        "desc": "Foydalanuvchilarga yuborilgan bildirishnomalar. Firebase push orqali.",
    },
    "notification_user_status": {
        "label": "Bildirishnoma holati / Notification Status",
        "desc": "Har bir foydalanuvchining bildirishnomani o'qigan/o'qimagan holati.",
    },
    "access_tokens": {
        "label": "Access Tokens",
        "desc": "Foydalanuvchi autentifikatsiya tokenlari (30 kun amal qiladi).",
    },
}

ENUM_FIELDS = {
    "users.user_type": {
        "label": "Foydalanuvchi turi",
        "values": [e.value for e in UserType],
        "meaning": (
            "USER=oddiy foydalanuvchi, SUPERADMIN=bosh admin, ADMIN=admin, "
            "MANAGER=menejer, SUPERVISOR=nazoratchi, AGENT=sotuv agenti, "
            "DELIVERER=yetkazib beruvchi, VENDOR_AGENT=yetkazib beruvchi agenti, "
            "CLIENT=mijoz, DEALER=diler, FACTORY=zavod, CEO=rahbar, "
            "FINANCIST=moliya xodimi, WAREHOUSE=ombor xodimi, SALESMAN=sotuvchi, "
            "CASHIER=kassir, HR=kadrlar bo'limi, MARKETING=marketing xodimi, "
            "EXTERNAL_SELLER=tashqi sotuvchi, MERCHANDISER=merchandayser"
        ),
    },
    "users.user_status": {
        "label": "Foydalanuvchi holati",
        "values": [e.value for e in UserStatus],
        "meaning": "ACTIVE=faol, INACTIVE=faol emas, PENDING=kutmoqda, BLOCKED=bloklangan",
    },
}

RELATIONSHIPS = [
    ("users.company_id", "companies.id", "many-to-one: har bir foydalanuvchi bitta kompaniyaga tegishli, bitta kompaniyada ko'p foydalanuvchi bor"),
    ("users.manager_id", "users.id", "many-to-one (self): foydalanuvchining menejeri/rahbari (o'z-o'ziga havola)"),
    ("locations.user_id", "users.id", "many-to-one: har bir joylashuv ma'lum bir foydalanuvchiga tegishli"),
    ("devices.user_id", "users.id", "many-to-one: har bir qurilma ma'lum bir foydalanuvchiga tegishli"),
    ("working_sessions.user_id", "users.id", "many-to-one: har bir sessiya ma'lum bir foydalanuvchiga tegishli"),
    ("security_keys.company_id", "companies.id", "one-to-one: har bir kompaniyaning bitta security key'i bor"),
    ("notification_user_status.notification_id", "notifications.id", "many-to-one: bildirishnomaning o'qilish holati"),
    ("notification_user_status.user_id", "users.id", "many-to-one: qaysi foydalanuvchi o'qiganligi"),
    ("notifications.company_id", "companies.id", "many-to-one: bildirishnoma kompaniyaga tegishli"),
    ("app_versions.app_id", "apps.id", "many-to-one: versiya ma'lum bir ilovaga tegishli"),
]

SEMANTIC_HINTS = [
    {
        "concept": "xodim, hodim, employee, ishchi, xodimlar",
        "sql_hint": "users WHERE user_type IN ('AGENT','SUPERVISOR','MANAGER','SALESMAN','DELIVERER','WAREHOUSE','MARKETING','HR','FINANCIST','CASHIER','MERCHANDISER','EXTERNAL_SELLER','VENDOR_AGENT')",
        "explanation": "USER, SUPERADMIN, ADMIN, CLIENT, DEALER, FACTORY, CEO - bular xodim hisoblanmaydi",
    },
    {
        "concept": "agent, agentlar, agents",
        "sql_hint": "users WHERE user_type = 'AGENT'",
    },
    {
        "concept": "faollik, aktivlik, activity, eng faol, ko'p faollik",
        "sql_hint": "working_sessions jadvalidagi sessionlar soni. JOIN users with working_sessions, COUNT(working_sessions.id), GROUP BY users.id",
        "explanation": "working_sessions jadvalidagi har bir qator bitta sessiyani (ilova ochilishi) bildiradi. 'Faollik' deganda aynan shu sessiyalar soni nazarda tutiladi.",
    },
    {
        "concept": "menejer, manager, rahbar, supervisor, nazoratchi",
        "sql_hint": "users.user_type IN ('MANAGER','SUPERVISOR','ADMIN') yoki users.manager_id orqali bog'lanish",
    },
    {
        "concept": "kompaniya, company, firma, tashkilot",
        "sql_hint": "companies jadvalidan. Foydalanuvchilar company_id orqali bog'langan.",
    },
    {
        "concept": "bildirishnoma, notification, xabar, habar",
        "sql_hint": "notifications jadvalidan. O'qilgan/o'qilmaganligi notification_user_status da.",
    },
    {
        "concept": "qurilma, device, telefon, telefo",
        "sql_hint": "devices jadvalidan. Foydalanuvchiga device.user_id orqali bog'lanadi.",
    },
    {
        "concept": "ilova versiya, app version, yangilanish, update",
        "sql_hint": "app_versions jadvalidan. apps jadvali bilan app_id orqali bog'lanadi.",
    },
    {
        "concept": "qancha, nechta, soni, count, royxat, list, hamma, barcha",
        "sql_hint": "COUNT() yoki SELECT bilan ishlating",
    },
    {
        "concept": "eng ko'p, eng kam, top, yuqori, past, birinchi, oxirgi",
        "sql_hint": "ORDER BY ... DESC/ASC LIMIT ... bilan ishlating",
    },
    {
        "concept": "bugungi, bugun, today, shu kun, sana, date, vaqt, qachon",
        "sql_hint": "CURRENT_DATE, NOW(), yoki created_at, updated_at ustunlaridan foydalaning",
    },
    {
        "concept": "faol, aktiv, active, is_active",
        "sql_hint": "user_status = 'ACTIVE' yoki is_active = True tekshirish",
    },
]


def _build_db_map() -> str:
    lines = []
    lines.append("# MX-Soft Distr Ma'lumotlar Ombori Xaritasi / Database Map")
    lines.append("")

    for table_name, table in Base.metadata.tables.items():
        meta = TABLE_META.get(table_name, {})
        label = meta.get("label", table_name)
        desc = meta.get("desc", "")
        lines.append(f"## {table_name} — {label}")
        if desc:
            lines.append(f"**{desc}**")
        lines.append("")

        lines.append("Ustunlar / Columns:")
        for col in table.columns:
            parts = [f"- **{col.name}**"]
            parts.append(f"`{col.type}`")

            if col.primary_key:
                parts.append("PK")
            if col.nullable:
                parts.append("nullable")
            else:
                parts.append("required")
            if col.default is not None:
                default_val = col.default.arg if hasattr(col.default, 'arg') and not callable(col.default.arg) else ""
                if default_val != "":
                    parts.append(f"default={default_val}")

            fks = [(fk.column.table.name, fk.column.name) for fk in col.foreign_keys]
            for ft, fc in fks:
                parts.append(f"FK->{ft}.{fc}")

            col_full_name = f"{table_name}.{col.name}"
            if col_full_name in ENUM_FIELDS:
                ef = ENUM_FIELDS[col_full_name]
                parts.append(f"qiymatlar: {ef['values']}")
                parts.append(f"({ef['meaning']})")

            lines.append("  " + " | ".join(parts))

        lines.append("")
        rels = [r for r in RELATIONSHIPS if r[0].startswith(f"{table_name}.")]
        if rels:
            lines.append("Bog'lanishlar / Relationships:")
            for r in rels:
                lines.append(f"  - {r[0]} {r[1]} : {r[2]}")
            lines.append("")

    lines.append("---")
    lines.append("## Semantik ko'rsatmalar / Semantic Hints")
    lines.append("Quyidagi tushunchalar va ularning SQL mapping'laridan foydalaning:")
    lines.append("")
    for hint in SEMANTIC_HINTS:
        concept = hint["concept"]
        sql_hint = hint["sql_hint"]
        lines.append(f"- **'{concept}'** {sql_hint}")
        if "explanation" in hint:
            lines.append(f"  Izoh: {hint['explanation']}")
    lines.append("")

    lines.append("---")
    lines.append("## Muhim eslatmalar / Important Notes")
    lines.append("- Barcha jadvallarda 'id', 'created_at', 'updated_at', 'deleted_at' ustunlari bor (Base dan meros).")
    lines.append("- deleted_at NULL bolsa, yozuv ochirilmagan (faol). Agar kerak bolmasa, WHERE deleted_at IS NULL qoshiling.")
    lines.append("- updated_at NULL bolishi mumkin (hech qachon yangilanmagan bolsa).")
    lines.append("- 'user' deyilganda users jadvali nazarda tutiladi.")
    lines.append("- Savol tilida javob bering (ozbek, rus yoki ingliz).")
    lines.append("- Natijalarni 100 tadan kop bolmasligi uchun LIMIT qoshiling.")
    lines.append("- SUM, COUNT, AVG kabi agregat funksiyalardan foydalanish mumkin.")

    return "\n".join(lines)


def _clean_sql(text: str) -> str:
    text = re.sub(r'^```sql\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def validate_sql(sql: str) -> str:
    cleaned = sql.strip()
    cleaned = re.sub(r'--.*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    forbidden = re.compile(
        r'^\s*(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|EXEC|EXECUTE|CALL|MERGE|GRANT|REVOKE)',
        re.IGNORECASE
    )
    if forbidden.match(cleaned):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    if not re.match(r'^\s*(SELECT|WITH)\b', cleaned, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    return cleaned


@router.post("")
async def ai_query(
    body: AIQueryRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured. Set it in .env file.")

    async with AsyncClient() as client:
        classify_resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You classify questions into exactly one category: 'data' or 'general'.\n"
                            "'data' = question asks about the database content, records, counts, users, companies, "
                            "agents, locations, sessions, notifications, devices, statistics, or any data stored in the system.\n"
                            "'general' = greeting, introduction, who-are-you, what-can-you-do, casual chat, "
                            "or anything not requesting specific database information.\n"
                            "Reply with ONLY one word: 'data' or 'general'."
                        ),
                    },
                    {"role": "user", "content": body.question},
                ],
                "temperature": 0,
                "max_tokens": 10,
            },
            timeout=15,
        )

        if classify_resp.status_code != 200:
            category = "data"
        else:
            category = classify_resp.json()["choices"][0]["message"]["content"].strip().lower()
            if category not in ("data", "general"):
                category = "data"

        if category == "general":
            chat_resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are MX Soft Agent an AI assistant for the MX-Soft Distr dashboard. "
                                "You help users with the distribution management system. "
                                "Answer conversationally, be friendly and concise. "
                                "Respond in the same language as the question. "
                                "IMPORTANT: You ONLY speak Uzbek (zbek), Russian (sskiy), and English. "
                                "If asked in any other language, reply in English. "
                                "Sign your response with '- MX Soft Agent' at the end."
                            ),
                        },
                        {"role": "user", "content": body.question},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500,
                },
                timeout=30,
            )

            if chat_resp.status_code != 200:
                answer = "I'm MX Soft Agent. How can I help you?"
            else:
                answer = chat_resp.json()["choices"][0]["message"]["content"].strip()

            return {
                "sql": None,
                "answer": answer,
                "formatted": answer,
                "format": "markdown",
                "count": None,
                "data": None,
            }

    db_map = _build_db_map()

    system_prompt = (
        "You are MX Soft Agent an AI assistant for the MX-Soft Distr dashboard.\n\n"
        "Below is the complete database map with descriptions, relationships, and semantic hints.\n"
        "Use it to convert natural language questions into PostgreSQL SQL queries.\n\n"
        f"{db_map}\n\n"
        "INSTRUCTIONS:\n"
        "- Return ONLY the SQL query, no explanations, no markdown\n"
        "- Use ONLY SELECT statements (read-only access)\n"
        "- Use exact table and column names as shown\n"
        "- Default to LIMIT 100 unless the question asks for more or fewer\n"
        "- For counting questions use COUNT(*)\n"
        "- For 'eng kop/eng kam/top' questions use ORDER BY + LIMIT\n"
        "- Use COALESCE for nullable fields when aggregating\n"
        "- Respond in the same language as the question\n"
        "- IMPORTANT: You ONLY output SQL code here, nothing else. The answer in natural language will be generated separately.\n"
    )

    async with AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": body.question},
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
            },
            timeout=60,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"AI service error: {resp.text}")

    groq_result = resp.json()
    raw_sql = groq_result["choices"][0]["message"]["content"]
    sql = _clean_sql(raw_sql)
    sql = validate_sql(sql)

    try:
        result_proxy = await session.execute(sql_text(sql))
        rows = result_proxy.fetchall()
        columns = result_proxy.keys()
        data = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query error: {str(e)}")

    data_str = "\n".join(str(row) for row in data[:20])
    total_count = len(data)
    summary_prompt = (
        "You are MX Soft Agent a helpful data analyst for the MX-Soft Distr dashboard.\n\n"
        f"User question: {body.question}\n"
        f"SQL query used: {sql}\n"
        f"Total rows returned: {total_count}\n"
        f"Data (first 20 rows):\n{data_str}\n\n"
        "Answer in the same language as the question.\n"
        "Include numbers and key facts. Be specific and helpful.\n"
        "IMPORTANT: You ONLY speak Uzbek (zbek), Russian (sskiy), and English.\n"
        "If asked in any other language, reply in English.\n"
        "Sign your response with '- MX Soft Agent' at the end.\n\n"
        "Return your answer as clean Markdown. Follow these rules:\n"
        "- **Bold** for numbers and key values\n"
        "- Use | tables | when showing row-by-row data\n"
        "- Use - bullets for lists\n"
        "- Clean spacing between sections\n"
        "- NO code blocks around the whole response\n"
        "- NO JSON wrapping\n"
        "- NO HTML tags\n"
        "- Just pure, beautiful Markdown"
    )

    async with AsyncClient() as client:
        resp2 = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are MX Soft Agent an expert at writing clean, beautiful Markdown. You ONLY speak Uzbek, Russian, and English."},
                    {"role": "user", "content": summary_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
            },
            timeout=60,
        )

    if resp2.status_code != 200:
        answer = f"Found {total_count} result(s). - MX Soft Agent"
        formatted = answer
    else:
        formatted = resp2.json()["choices"][0]["message"]["content"].strip()
        formatted = re.sub(r'^```(?:markdown)?\s*', '', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'\s*```$', '', formatted)
        formatted = formatted.strip()
        answer = re.sub(r'\*\*(.+?)\*\*', r'\1', formatted)
        answer = re.sub(r'\*(.+?)\*', r'\1', answer)
        answer = re.sub(r'`(.+?)`', r'\1', answer)
        answer = re.sub(r'^###?\s*', '', answer, flags=re.MULTILINE)
        answer = re.sub(r'\|', ' ', answer)
        answer = re.sub(r'^[-*]\s', '', answer, flags=re.MULTILINE)
        answer = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', answer)
        answer = re.sub(r'__(\S+?)__', r'\1', answer)
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        answer = answer.strip()

    return {
        "sql": sql,
        "answer": answer,
        "formatted": formatted,
        "format": "markdown",
        "count": total_count,
        "data": data,
    }
