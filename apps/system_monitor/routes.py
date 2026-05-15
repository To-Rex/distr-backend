import platform
import time
from datetime import datetime, timezone

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.system_monitor.schemas import (
    CpuInfo,
    DatabaseInfo,
    DbConnection,
    DbTableInfo,
    DiskInfo,
    DiskPartition,
    MemoryInfo,
    NetworkInterface,
    ProcessInfo,
    SystemInfo,
    SystemMonitorResponse,
)
from config.database import get_async_session

router = APIRouter(
    prefix="/system-monitor",
    tags=["System Monitor"],
)


@router.get("/", response_model=SystemMonitorResponse)
async def get_system_info():
    cpu_freq = psutil.cpu_freq()

    cpu_info = CpuInfo(
        physical_cores=psutil.cpu_count(logical=False) or 0,
        total_cores=psutil.cpu_count(logical=True) or 0,
        percent_usage=psutil.cpu_percent(interval=0.5),
        per_core_percent=psutil.cpu_percent(interval=0.5, percpu=True),
        frequency_current=cpu_freq.current if cpu_freq else None,
        frequency_min=cpu_freq.min if cpu_freq else None,
        frequency_max=cpu_freq.max if cpu_freq else None,
    )

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    memory_info = MemoryInfo(
        total=mem.total,
        available=mem.available,
        used=mem.used,
        percent=mem.percent,
        swap_total=swap.total,
        swap_used=swap.used,
        swap_free=swap.free,
        swap_percent=swap.percent,
    )

    disk_infos = []
    partitions = []
    seen_devices = set()
    for partition in psutil.disk_partitions():
        partitions.append(
            DiskPartition(
                device=partition.device,
                mountpoint=partition.mountpoint,
                fstype=partition.fstype,
                opts=partition.opts,
            )
        )
        if partition.device and partition.device not in seen_devices:
            seen_devices.add(partition.device)
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_infos.append(
                    DiskInfo(
                        total=usage.total,
                        used=usage.used,
                        free=usage.free,
                        percent=usage.percent,
                    )
                )
            except (PermissionError, OSError):
                pass

    net_io = psutil.net_io_counters(pernic=True)
    network = []
    for iface, counters in net_io.items():
        network.append(
            NetworkInterface(
                name=iface,
                bytes_sent=counters.bytes_sent,
                bytes_recv=counters.bytes_recv,
                packets_sent=counters.packets_sent,
                packets_recv=counters.packets_recv,
            )
        )

    boot_time_ts = psutil.boot_time()
    system_info = SystemInfo(
        hostname=platform.node(),
        os_name=platform.system(),
        os_version=platform.version(),
        architecture=platform.machine(),
        processor=platform.processor() or "N/A",
        python_version=platform.python_version(),
        boot_time=boot_time_ts,
        uptime_seconds=time.time() - boot_time_ts,
    )

    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            processes.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info["name"] or "unknown",
                    cpu_percent=info["cpu_percent"] or 0.0,
                    memory_percent=info["memory_percent"] or 0.0,
                    status=info["status"] or "unknown",
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda p: p.cpu_percent, reverse=True)
    top_processes = processes[:20]

    return SystemMonitorResponse(
        system=system_info,
        cpu=cpu_info,
        memory=memory_info,
        disks=disk_infos,
        partitions=partitions,
        network=network,
        top_processes=top_processes,
    )


@router.get("/cpu", response_model=CpuInfo)
async def get_cpu_info():
    cpu_freq = psutil.cpu_freq()
    return CpuInfo(
        physical_cores=psutil.cpu_count(logical=False) or 0,
        total_cores=psutil.cpu_count(logical=True) or 0,
        percent_usage=psutil.cpu_percent(interval=0.5),
        per_core_percent=psutil.cpu_percent(interval=0.5, percpu=True),
        frequency_current=cpu_freq.current if cpu_freq else None,
        frequency_min=cpu_freq.min if cpu_freq else None,
        frequency_max=cpu_freq.max if cpu_freq else None,
    )


@router.get("/memory", response_model=MemoryInfo)
async def get_memory_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return MemoryInfo(
        total=mem.total,
        available=mem.available,
        used=mem.used,
        percent=mem.percent,
        swap_total=swap.total,
        swap_used=swap.used,
        swap_free=swap.free,
        swap_percent=swap.percent,
    )


@router.get("/disk", response_model=list[DiskInfo])
async def get_disk_info():
    result = []
    seen_devices = set()
    for partition in psutil.disk_partitions():
        if partition.device and partition.device not in seen_devices:
            seen_devices.add(partition.device)
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                result.append(
                    DiskInfo(
                        total=usage.total,
                        used=usage.used,
                        free=usage.free,
                        percent=usage.percent,
                    )
                )
            except (PermissionError, OSError):
                pass
    return result


@router.get("/database", response_model=DatabaseInfo)
async def get_database_info(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(text("SELECT current_database()"))
    db_name = result.scalar()

    result = await session.execute(text("SELECT pg_database_size(current_database())"))
    db_size_bytes = result.scalar()

    result = await session.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
    db_size_pretty = result.scalar()

    result = await session.execute(text("SHOW server_version"))
    server_version = result.scalar()

    result = await session.execute(text("SELECT pg_postmaster_start_time()"))
    start_time = result.scalar()
    uptime_seconds = (datetime.now(timezone.utc) - start_time.replace(tzinfo=timezone.utc)).total_seconds()
    uptime_pretty = f"{int(uptime_seconds // 86400)}d {int((uptime_seconds % 86400) // 3600)}h {int((uptime_seconds % 3600) // 60)}m"

    result = await session.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
    active_conns = result.scalar()

    result = await session.execute(text("SHOW max_connections"))
    max_conns = int(result.scalar())

    result = await session.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'"))
    current_tx = result.scalar()

    result = await session.execute(text(
        "SELECT ROUND(COALESCE(SUM(heap_blks_hit)::decimal / NULLIF(SUM(heap_blks_hit + heap_blks_read), 0), 0) * 100, 2) "
        "FROM pg_statio_user_tables"
    ))
    cache_hit = result.scalar()

    result = await session.execute(text(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
    ))
    total_tables = result.scalar()

    result = await session.execute(text(
        "SELECT pid, usename, application_name, client_addr::text, state, "
        "query, extract(epoch FROM (now() - state_change)) AS connected_seconds "
        "FROM pg_stat_activity WHERE pid <> pg_backend_pid() ORDER BY state_change DESC"
    ))
    connections = []
    for row in result:
        connections.append(DbConnection(
            pid=row.pid,
            username=row.usename,
            application_name=row.application_name,
            client_address=row.client_addr,
            state=row.state,
            query=row.query,
            connected_seconds=row.connected_seconds,
        ))

    result = await session.execute(text(
        "SELECT relname AS table_name, "
        "COALESCE(n_live_tup, 0) AS row_count, "
        "pg_size_pretty(pg_total_relation_size(relid)) AS total_size, "
        "pg_size_pretty(pg_relation_size(relid)) AS table_size, "
        "pg_size_pretty(pg_indexes_size(relid)) AS index_size "
        "FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC"
    ))
    tables = []
    for row in result:
        tables.append(DbTableInfo(
            table_name=row.table_name,
            row_count=row.row_count,
            total_size=row.total_size,
            table_size=row.table_size,
            index_size=row.index_size,
        ))

    return DatabaseInfo(
        database_name=db_name,
        database_size=db_size_pretty,
        database_size_bytes=db_size_bytes,
        server_version=server_version,
        server_uptime=uptime_pretty,
        server_uptime_seconds=uptime_seconds,
        active_connections=active_conns,
        max_connections=max_conns,
        current_transactions=current_tx,
        cache_hit_ratio=cache_hit,
        total_tables=total_tables,
        connections=connections,
        tables=tables,
    )


@router.get("/network", response_model=list[NetworkInterface])
async def get_network_info():
    net_io = psutil.net_io_counters(pernic=True)
    result = []
    for iface, counters in net_io.items():
        result.append(
            NetworkInterface(
                name=iface,
                bytes_sent=counters.bytes_sent,
                bytes_recv=counters.bytes_recv,
                packets_sent=counters.packets_sent,
                packets_recv=counters.packets_recv,
            )
        )
    return result


@router.get("/processes", response_model=list[ProcessInfo])
async def get_processes(limit: int = 20):
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            processes.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info["name"] or "unknown",
                    cpu_percent=info["cpu_percent"] or 0.0,
                    memory_percent=info["memory_percent"] or 0.0,
                    status=info["status"] or "unknown",
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda p: p.cpu_percent, reverse=True)
    return processes[:limit]
