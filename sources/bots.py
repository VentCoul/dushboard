"""Моніторинг VPS і Telegram-ботів: psutil-метрики + systemctl-статус."""
import subprocess
import time

import psutil

import config


def vps_metrics():
    """CPU / RAM / диск / аптайм."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime_sec = time.time() - psutil.boot_time()
    days, rem = divmod(int(uptime_sec), 86400)
    hours = rem // 3600
    return {
        "cpu_pct": psutil.cpu_percent(interval=0.3),
        "ram_pct": mem.percent,
        "ram_used_gb": round(mem.used / 1024**3, 1),
        "ram_total_gb": round(mem.total / 1024**3, 1),
        "disk_pct": disk.percent,
        "disk_used_gb": round(disk.used / 1024**3, 1),
        "disk_total_gb": round(disk.total / 1024**3, 1),
        "uptime": f"{days}д {hours}год",
    }


def bot_statuses():
    """Статус кожного systemd-сервісу з BOT_SERVICES через `systemctl is-active`."""
    statuses = []
    for name in config.BOT_SERVICES:
        try:
            out = subprocess.run(
                ["systemctl", "is-active", name],
                capture_output=True, text=True, timeout=5,
            )
            state = out.stdout.strip() or "unknown"
        except Exception:
            state = "недоступно"  # локально без systemd (напр. macOS)
        statuses.append({"name": name, "active": state == "active", "state": state})
    return statuses
