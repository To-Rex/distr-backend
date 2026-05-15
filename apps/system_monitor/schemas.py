from typing import Optional
from pydantic import BaseModel


class CpuInfo(BaseModel):
    physical_cores: int
    total_cores: int
    percent_usage: float
    per_core_percent: list[float]
    frequency_current: Optional[float]
    frequency_min: Optional[float]
    frequency_max: Optional[float]


class MemoryInfo(BaseModel):
    total: int
    available: int
    used: int
    percent: float
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float


class DiskInfo(BaseModel):
    total: int
    used: int
    free: int
    percent: float


class DiskPartition(BaseModel):
    device: str
    mountpoint: str
    fstype: Optional[str]
    opts: str


class NetworkInterface(BaseModel):
    name: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


class SystemInfo(BaseModel):
    hostname: str
    os_name: str
    os_version: str
    architecture: str
    processor: str
    python_version: str
    boot_time: float
    uptime_seconds: float


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str


class DbConnection(BaseModel):
    pid: int
    username: Optional[str]
    application_name: Optional[str]
    client_address: Optional[str]
    state: Optional[str]
    query: Optional[str]
    connected_seconds: Optional[float]


class DbTableInfo(BaseModel):
    table_name: str
    row_count: Optional[int]
    total_size: str
    table_size: str
    index_size: str


class DatabaseInfo(BaseModel):
    database_name: str
    database_size: str
    database_size_bytes: int
    server_version: str
    server_uptime: str
    server_uptime_seconds: float
    active_connections: int
    max_connections: int
    current_transactions: int
    cache_hit_ratio: Optional[float]
    total_tables: int
    connections: list[DbConnection]
    tables: list[DbTableInfo]


class SystemMonitorResponse(BaseModel):
    system: SystemInfo
    cpu: CpuInfo
    memory: MemoryInfo
    disks: list[DiskInfo]
    partitions: list[DiskPartition]
    network: list[NetworkInterface]
    top_processes: list[ProcessInfo]
