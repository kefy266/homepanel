import shutil
import subprocess
import psutil

def gpu_stats():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2, check=True
        )
        line = result.stdout.strip().splitlines()[0]
        name, util, used, total, temp = [part.strip() for part in line.split(",", 4)]
        return {
            "available": True, "name": name,
            "usage": float(util), "memory_used_mb": float(used),
            "memory_total_mb": float(total), "temperature_c": float(temp)
        }
    except Exception:
        return {"available": False}

def collect_stats():
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    cpu_temp = None
    try:
        temps = psutil.sensors_temperatures()
        for entries in temps.values():
            for entry in entries:
                if entry.current is not None:
                    cpu_temp = round(entry.current, 1)
                    break
            if cpu_temp is not None:
                break
    except Exception:
        pass
    return {
        "cpu": {"usage": psutil.cpu_percent(interval=0.15), "logical_cores": psutil.cpu_count()},
        "memory": {"used": mem.used, "total": mem.total, "percent": mem.percent},
        "disk": {"used": disk.used, "total": disk.total, "percent": round(disk.used / disk.total * 100, 1)},
        "temperature_c": cpu_temp,
        "gpu": gpu_stats()
    }
