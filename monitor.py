import time
import json
import os
import platform
import subprocess
import requests
from datetime import datetime


# =========================================================
# KONFIGURASI 8 HOST
# =========================================================

HOSTS = [
    {
        "id": 1,
        "name": "My Server Gwe",
        "address": "192.168.122.201",
        "type": "LOCAL"
    },
    {
        "id": 2,
        "name": "Google",
        "address": "google.com",
        "type": "PUBLIC WEB"
    },
    {
        "id": 3,
        "name": "GitHub",
        "address": "github.com",
        "type": "DEVELOPER PLATFORM"
    },
    {
        "id": 4,
        "name": "Cloudflare",
        "address": "cloudflare.com",
        "type": "NETWORK CLOUD"
    },
    {
        "id": 5,
        "name": "Microsoft",
        "address": "microsoft.com",
        "type": "PUBLIC WEB"
    },
    {
        "id": 6,
        "name": "YouTube",
        "address": "youtube.com",
        "type": "VIDEO CONTENT"
    },
    {
        "id": 7,
        "name": "Wikipedia",
        "address": "wikipedia.org",
        "type": "STUDY PLATFORM"
    },
    {
        "id": 8,
        "name": "OpenAI",
        "address": "openai.com",
        "type": "AI PLATFORM"
    }
]


# =========================================================
# KONFIGURASI FILE
# =========================================================

STATUS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "status.json"
)


# =========================================================
# KONFIGURASI N8N
# =========================================================
#
# SEKARANG:
# Gunakan webhook-test karena workflow masih dalam tahap testing.
#
# Setelah workflow n8n sudah ACTIVE, ubah menjadi:
#
# http://localhost:5678/webhook/8host
#
# =========================================================

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/8host"


# =========================================================
# PENYIMPANAN STATUS
# =========================================================

down_since = {}
previous_status = {}


# =========================================================
# CEK HOST DENGAN PING
# =========================================================

def check_host(host):
    target = host["address"]

    if platform.system().lower() == "windows":
        command = [
            "ping",
            "-n",
            "1",
            "-w",
            "2000",
            target
        ]
    else:
        command = [
            "ping",
            "-c",
            "1",
            "-W",
            "2",
            target
        ]

    start = time.perf_counter()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        elapsed = round(
            (time.perf_counter() - start) * 1000,
            2
        )

        if result.returncode == 0:
            return "online", elapsed

        return "offline", None

    except Exception:
        return "offline", None


# =========================================================
# FORMAT DOWNTIME
# =========================================================

def format_downtime(seconds):
    seconds = int(seconds)

    days = seconds // 86400
    seconds %= 86400

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60
    seconds %= 60

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"

    if minutes > 0:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


# =========================================================
# KIRIM DATA KE N8N
# =========================================================

def send_to_n8n(data):

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=data,
            timeout=5
        )

        print(
            f"[N8N] Data terkirim | "
            f"Status HTTP: {response.status_code}"
        )

    except requests.exceptions.RequestException as error:

        print(
            f"[N8N] Gagal mengirim data: {error}"
        )


# =========================================================
# MONITORING UTAMA
# =========================================================

def monitor():

    results = []

    now = datetime.now()

    for host in HOSTS:

        # -------------------------------------------------
        # CEK HOST
        # -------------------------------------------------

        status, response = check_host(host)

        # -------------------------------------------------
        # STATUS SEBELUMNYA
        # -------------------------------------------------

        old_status = previous_status.get(
            host["id"],
            status
        )

        # -------------------------------------------------
        # JIKA OFFLINE
        # -------------------------------------------------

        if status == "offline":

            # Jika baru pertama kali DOWN,
            # simpan waktu mulai downtime.

            if host["id"] not in down_since:

                down_since[host["id"]] = time.time()

            downtime_seconds = (
                time.time()
                - down_since[host["id"]]
            )

            downtime = format_downtime(
                downtime_seconds
            )

        # -------------------------------------------------
        # JIKA ONLINE
        # -------------------------------------------------

        else:

            downtime = "-"

            # Jika sebelumnya DOWN lalu sekarang ONLINE,
            # hitung total downtime.

            if host["id"] in down_since:

                downtime_seconds = (
                    time.time()
                    - down_since[host["id"]]
                )

                downtime = format_downtime(
                    downtime_seconds
                )

                del down_since[host["id"]]

        # -------------------------------------------------
        # KIRIM EVENT HANYA JIKA STATUS BERUBAH
        # -------------------------------------------------

        if old_status != status:

            event = {
                "event": "status_change",

                "id": host["id"],

                "name": host["name"],

                "address": host["address"],

                "type": host["type"],

                "oldStatus": old_status,

                "status": status,

                "response": response,

                "downtime": downtime,

                "timestamp": datetime.now().isoformat()
            }

            print()
            print(">>> STATUS BERUBAH <<<")

            print(
                f"Host       : {host['name']}"
            )

            print(
                f"Status     : "
                f"{old_status.upper()} -> "
                f"{status.upper()}"
            )

            print(
                f"Downtime   : {downtime}"
            )

            print()

            # Kirim ke n8n

            send_to_n8n(event)

        # -------------------------------------------------
        # SIMPAN STATUS TERAKHIR
        # -------------------------------------------------

        previous_status[host["id"]] = status

        # -------------------------------------------------
        # MASUKKAN DATA KE STATUS.JSON
        # -------------------------------------------------

        results.append({

            "id": host["id"],

            "name": host["name"],

            "type": host["type"],

            "address": host["address"],

            "status": status,

            "response": response,

            "downtime": downtime

        })

    # =====================================================
    # DATA UNTUK WEBSITE
    # =====================================================

    data = {

        "lastUpdate": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "totalHost": len(results),

        "hosts": results

    }

    # =====================================================
    # SIMPAN STATUS.JSON
    # =====================================================

    try:

        with open(
            STATUS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    except Exception as error:

        print(
            f"[FILE] Gagal menyimpan status.json: {error}"
        )

    # =====================================================
    # TAMPILKAN HASIL DI TERMINAL
    # =====================================================

    print()
    print("=" * 65)

    print(
        f"NETWORK MONITORING | "
        f"{now.strftime('%H:%M:%S')}"
    )

    print("=" * 65)

    for host in results:

        if host["status"] == "online":

            print(
                f"[ONLINE ] "
                f"{host['name']:<15} "
                f"{host['response']} ms"
            )

        else:

            print(
                f"[OFFLINE] "
                f"{host['name']:<15} "
                f"Downtime: {host['downtime']}"
            )

    print("=" * 65)


# =========================================================
# PROGRAM UTAMA
# =========================================================

print()
print("=" * 65)
print("             NETWORK MONITORING 8 HOST")
print("=" * 65)

print()
print("Monitoring dimulai...")
print("Interval pengecekan : 10 detik")
print(f"Status file         : {STATUS_FILE}")
print(f"n8n webhook          : {N8N_WEBHOOK_URL}")

print()
print("Tekan CTRL + C untuk menghentikan monitoring.")
print()


while True:

    try:

        monitor()

        time.sleep(10)

    except KeyboardInterrupt:

        print()
        print("=" * 65)
        print("Monitoring dihentikan.")
        print("=" * 65)
        break

    except Exception as error:

        print()
        print(
            f"[ERROR] Terjadi kesalahan: {error}"
        )

        print(
            "Monitoring akan dilanjutkan..."
        )

        time.sleep(10)