# MX-Soft Distr — Tizim Monitoring API

**Base URL:** `http://<host>:8002/api/v1/system-monitor`

Server resurslari (CPU, RAM, disk, tarmoq, jarayonlar, PostgreSQL) haqida real-time ma'lumot.

**Auth:** Kerak emas (ochiq).

---

## 1. To'liq tizim ma'lumoti

```
GET /api/v1/system-monitor/
```

**Response (200):**
```json
{
  "system": {
    "hostname": "server-1",
    "os_name": "Linux",
    "os_version": "#1 SMP...",
    "architecture": "x86_64",
    "processor": "Intel(R) Xeon(R)",
    "python_version": "3.11.0",
    "boot_time": 1704067200.0,
    "uptime_seconds": 864000.0
  },
  "cpu": {
    "physical_cores": 4,
    "total_cores": 8,
    "percent_usage": 25.5,
    "per_core_percent": [20.0, 30.0, 15.0, 35.0, ...],
    "frequency_current": 2400.0,
    "frequency_min": 800.0,
    "frequency_max": 3200.0
  },
  "memory": {
    "total": 8589934592,
    "available": 4294967296,
    "used": 4294967296,
    "percent": 50.0,
    "swap_total": 2147483648,
    "swap_used": 0,
    "swap_free": 2147483648,
    "swap_percent": 0.0
  },
  "disks": [
    { "total": 107374182400, "used": 53687091200, "free": 53687091200, "percent": 50.0 }
  ],
  "partitions": [
    { "device": "/dev/sda1", "mountpoint": "/", "fstype": "ext4", "opts": "rw,relatime" }
  ],
  "network": [
    { "name": "eth0", "bytes_sent": 1234567890, "bytes_recv": 9876543210, "packets_sent": 1000000, "packets_recv": 5000000 }
  ],
  "top_processes": [
    { "pid": 1234, "name": "python", "cpu_percent": 15.5, "memory_percent": 2.3, "status": "running" }
  ]
}
```

---

## 2. CPU ma'lumoti

```
GET /api/v1/system-monitor/cpu
```

**Response (200):** `CpuInfo` obyekti

---

## 3. RAM ma'lumoti

```
GET /api/v1/system-monitor/memory
```

**Response (200):** `MemoryInfo` obyekti (RAM + Swap)

---

## 4. Disk ma'lumoti

```
GET /api/v1/system-monitor/disk
```

**Response (200):** `List[DiskInfo]`

---

## 5. Tarmoq ma'lumoti

```
GET /api/v1/system-monitor/network
```

**Response (200):** `List[NetworkInterface]`

---

## 6. Jarayonlar

```
GET /api/v1/system-monitor/processes?limit=20
```

| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| **Query** ||||
| limit | int | Yo'q (20) | Nechta jarayon |

**Response (200):** `List[ProcessInfo]` — CPU foizi bo'yicha kamayish tartibida

---

## 7. Ma'lumotlar bazasi

```
GET /api/v1/system-monitor/database
```

PostgreSQL haqida to'liq statistika.

**Response (200):**
```json
{
  "database_name": "mx_soft_distr",
  "database_size": "512 MB",
  "database_size_bytes": 536870912,
  "server_version": "16.1",
  "server_uptime": "10d 5h 30m",
  "server_uptime_seconds": 889800.0,
  "active_connections": 5,
  "max_connections": 100,
  "current_transactions": 3,
  "cache_hit_ratio": 98.5,
  "total_tables": 15,
  "connections": [
    {
      "pid": 5678,
      "username": "mxsoft",
      "application_name": "PostgreSQL JDBC",
      "client_address": "10.0.0.1",
      "state": "active",
      "query": "SELECT * FROM users WHERE ...",
      "connected_seconds": 3600.0
    }
  ],
  "tables": [
    {
      "table_name": "users",
      "row_count": 1500,
      "total_size": "128 MB",
      "table_size": "96 MB",
      "index_size": "32 MB"
    }
  ]
}
```

---

## Schema tafsilotlari

### CpuInfo
| Maydon | Turi | Tavsif |
|--------|------|--------|
| physical_cores | int | Fizik yadrolar soni |
| total_cores | int | Mantiqiy yadrolar soni |
| percent_usage | float | Umumiy CPU foizi |
| per_core_percent | list[float] | Har bir yadro foizi |
| frequency_current | float? | Joriy chastota (MHz) |
| frequency_min | float? | Minimal chastota |
| frequency_max | float? | Maksimal chastota |

### MemoryInfo
| Maydon | Turi | Tavsif |
|--------|------|--------|
| total | int | Jami RAM (bayt) |
| available | int | Mavjud RAM |
| used | int | Ishlatilgan RAM |
| percent | float | Ishlatilgan foiz |
| swap_total | int | Jami swap |
| swap_used | int | Ishlatilgan swap |
| swap_free | int | Bo'sh swap |
| swap_percent | float | Swap foizi |

### DatabaseInfo
| Maydon | Turi | Tavsif |
|--------|------|--------|
| database_name | str | DB nomi |
| database_size | str | O'lcham (pretty) |
| database_size_bytes | int | O'lcham (bayt) |
| server_version | str | PostgreSQL versiyasi |
| server_uptime | str | Ish vaqti (pretty) |
| active_connections | int | Faol ulanishlar |
| max_connections | int | Maksimal ulanishlar |
| current_transactions | int | Joriy tranzaksiyalar |
| cache_hit_ratio | float? | Kesh hit foizi |
| total_tables | int | Jadvallar soni |
| connections | list[DbConnection] | Ulanishlar ro'yxati |
| tables | list[DbTableInfo] | Jadval statistikasi |
