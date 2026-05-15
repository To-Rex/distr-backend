# System Monitor API

Server holati, xotira, protsessor, disk, tarmoq va jarayonlar haqida to'liq ma'lumot olish uchun API.

**Base URL:** `/api/v1/system-monitor`

---

## To'liq sistema ma'lumotlari

```
GET /api/v1/system-monitor/
```

Barcha sistema ma'lumotlarini bitta javobda qaytaradi: CPU, RAM, Disk, Tarmoq, Processlar va OS info.

**Response:**

```json
{
  "system": {
    "hostname": "server-name",
    "os_name": "Linux",
    "os_version": "#1 SMP ...",
    "architecture": "x86_64",
    "processor": "Intel(R) ...",
    "python_version": "3.10.12",
    "boot_time": 1715200000.0,
    "uptime_seconds": 86400.0
  },
  "cpu": {
    "physical_cores": 4,
    "total_cores": 8,
    "percent_usage": 23.5,
    "per_core_percent": [20.0, 25.0, 22.0, 27.0, 21.0, 24.0, 23.0, 26.0],
    "frequency_current": 2400.0,
    "frequency_min": 800.0,
    "frequency_max": 3200.0
  },
  "memory": {
    "total": 16777216000,
    "available": 8388608000,
    "used": 8388608000,
    "percent": 50.0,
    "swap_total": 4294967296,
    "swap_used": 536870912,
    "swap_free": 3758096384,
    "swap_percent": 12.5
  },
  "disks": [
    {
      "total": 500000000000,
      "used": 250000000000,
      "free": 250000000000,
      "percent": 50.0
    }
  ],
  "partitions": [
    {
      "device": "/dev/sda1",
      "mountpoint": "/",
      "fstype": "ext4",
      "opts": "rw,relatime"
    }
  ],
  "network": [
    {
      "name": "eth0",
      "bytes_sent": 1073741824,
      "bytes_recv": 2147483648,
      "packets_sent": 1000000,
      "packets_recv": 2000000
    }
  ],
  "top_processes": [
    {
      "pid": 1234,
      "name": "python",
      "cpu_percent": 15.2,
      "memory_percent": 3.8,
      "status": "running"
    }
  ]
}
```

---

## Protsessor ma'lumotlari

```
GET /api/v1/system-monitor/cpu
```

**Response:**

```json
{
  "physical_cores": 4,
  "total_cores": 8,
  "percent_usage": 23.5,
  "per_core_percent": [20.0, 25.0, 22.0, 27.0, 21.0, 24.0, 23.0, 26.0],
  "frequency_current": 2400.0,
  "frequency_min": 800.0,
  "frequency_max": 3200.0
}
```

| Maydon | Turi | Tavsif |
|---|---|---|
| `physical_cores` | `int` | Fizik yadrolar soni |
| `total_cores` | `int` | Mantiqiy yadrolar soni (Hyper-Threading bilan) |
| `percent_usage` | `float` | Umumiy CPU yuklanishi (%) |
| `per_core_percent` | `float[]` | Har bir yadroning yuklanishi (%) |
| `frequency_current` | `float?` | Joriy chastota (MHz) |
| `frequency_min` | `float?` | Minimal chastota (MHz) |
| `frequency_max` | `float?` | Maksimal chastota (MHz) |

---

## Xotira ma'lumotlari

```
GET /api/v1/system-monitor/memory
```

**Response:**

```json
{
  "total": 16777216000,
  "available": 8388608000,
  "used": 8388608000,
  "percent": 50.0,
  "swap_total": 4294967296,
  "swap_used": 536870912,
  "swap_free": 3758096384,
  "swap_percent": 12.5
}
```

| Maydon | Turi | Tavsif |
|---|---|---|
| `total` | `int` | Umumiy RAM (bayt) |
| `available` | `int` | Mavjud RAM (bayt) |
| `used` | `int` | Foydalanilayotgan RAM (bayt) |
| `percent` | `float` | RAM yuklanishi (%) |
| `swap_total` | `int` | Umumiy Swap (bayt) |
| `swap_used` | `int` | Foydalanilayotgan Swap (bayt) |
| `swap_free` | `int` | Bo'sh Swap (bayt) |
| `swap_percent` | `float` | Swap yuklanishi (%) |

---

## Disk ma'lumotlari

```
GET /api/v1/system-monitor/disk
```

**Response:**

```json
[
  {
    "total": 500000000000,
    "used": 250000000000,
    "free": 250000000000,
    "percent": 50.0
  }
]
```

| Maydon | Turi | Tavsif |
|---|---|---|
| `total` | `int` | Umumiy disk hajmi (bayt) |
| `used` | `int` | Foydalanilgan joy (bayt) |
| `free` | `int` | Bo'sh joy (bayt) |
| `percent` | `float` | Bandlik (%) |

---

## Tarmoq ma'lumotlari

```
GET /api/v1/system-monitor/network
```

**Response:**

```json
[
  {
    "name": "eth0",
    "bytes_sent": 1073741824,
    "bytes_recv": 2147483648,
    "packets_sent": 1000000,
    "packets_recv": 2000000
  }
]
```

| Maydon | Turi | Tavsif |
|---|---|---|
| `name` | `str` | Interfeys nomi |
| `bytes_sent` | `int` | Yuborilgan baytlar |
| `bytes_recv` | `int` | Qabul qilingan baytlar |
| `packets_sent` | `int` | Yuborilgan paketlar |
| `packets_recv` | `int` | Qabul qilingan paketlar |

---

## Jarayonlar ro'yxati

```
GET /api/v1/system-monitor/processes?limit=20
```

**Query parametrlar:**

| Parametr | Birlamchi | Tavsif |
|---|---|---|
| `limit` | `20` | Qaytariladigan jarayonlar soni |

**Response:**

```json
[
  {
    "pid": 1234,
    "name": "python",
    "cpu_percent": 15.2,
    "memory_percent": 3.8,
    "status": "running"
  }
]
```

| Maydon | Turi | Tavsif |
|---|---|---|
| `pid` | `int` | Jarayon ID si |
| `name` | `str` | Jarayon nomi |
| `cpu_percent` | `float` | CPU dan foydalanish (%) |
| `memory_percent` | `float` | Xotiradan foydalanish (%) |
| `status` | `str` | Holati (running, sleeping, ...) |

Jarayonlar `cpu_percent` bo'yicha kamayish tartibida saralanadi.

---

## Texnik ma'lumotlar

- **Kutubxona:** `psutil >= 7.0.0`
- **Autentifikatsiya:** Talab qilinmaydi (ixtiyoriy qo'shish mumkin)
- **Barcha bayt qiymatlar** GB/MB ga o'tkazish uchun `value / (1024**3)` yoki `value / (1024**2)` formuladan foydalaning
