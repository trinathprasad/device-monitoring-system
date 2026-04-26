import psutil
import time
import requests

while True:
    data = {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "uptime": time.time() - psutil.boot_time(),
        "battery": psutil.sensors_battery().percent if psutil.sensors_battery() else 0,
        "status": "active"
    }

    requests.post("http://127.0.0.1:5000/api/data", json=data)

    time.sleep(10) 