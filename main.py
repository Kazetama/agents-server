import os
import re
import sys
import time
import shlex
import threading
import subprocess
import requests
import telebot
import docker
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip('/')

# Inisialisasi Bot Telegram
if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
    print("❌ ERROR: TELEGRAM_BOT_TOKEN belum diset dengan benar di file .env!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Parsing daftar User ID yang diperbolehkan secara dinamis & aman
ALLOWED_IDS = []
allowed_ids_raw = os.getenv("ALLOWED_TELEGRAM_IDS", "")
if allowed_ids_raw:
    try:
        ALLOWED_IDS = [int(x.strip()) for x in allowed_ids_raw.split(",") if x.strip()]
        print(f"🔒 ID Telegram Terotorisasi: {ALLOWED_IDS}")
    except ValueError as ve:
        print(f"⚠️ Kesalahan parsing ALLOWED_TELEGRAM_IDS: {ve}")

# Parsing ID Chat untuk notifikasi Alert
ALERT_CHAT_ID = None
alert_chat_raw = os.getenv("ALERT_CHAT_ID", "")
if alert_chat_raw:
    try:
        ALERT_CHAT_ID = int(alert_chat_raw.strip())
        print(f"🔔 Target ID Alert Chat: {ALERT_CHAT_ID}")
    except ValueError as ve:
        print(f"⚠️ Kesalahan parsing ALERT_CHAT_ID: {ve}")


# ==========================================
# 🛡️ SAFETY GUARDRAILS (KEAMANAN SISTEM)
# ==========================================

def is_command_safe(command: str) -> bool:
    """
    Melakukan pemeriksaan deterministik secara ketat terhadap perintah
    sebelum dieksekusi di subprocess host.
    """
    cmd = command.strip()
    
    # Wajib diawali dengan 'docker'
    if not cmd.lower().startswith("docker"):
        return False
        
    # Blokir operator chaining dan redirection shell
    forbidden_chars = [';', '&&', '||', '|', '&', '>', '<', '$', '`', '\n', '\r']
    for char in forbidden_chars:
        if char in cmd:
            print(f"🚨 Guardrail Pemicu: Menemukan karakter terlarang '{char}'")
            return False
            
    # Blokir kata kunci yang berpotensi membahayakan host filesystem
    dangerous_keywords = ["rm -rf", "sudo", "sh", "bash", "/etc", "/var/run", "docker.sock"]
    for kw in dangerous_keywords:
        if kw in cmd.lower():
            print(f"🚨 Guardrail Pemicu: Menemukan keyword terlarang '{kw}'")
            return False
            
    # Lakukan shlex parsing untuk memvalidasi argumen commands secara atomik
    try:
        parts = shlex.split(cmd)
        if not parts:
            return False
        if parts[0].lower() != "docker":
            return False
            
        # Periksa setiap parameter secara mendalam. 
        # Jangan izinkan parameter yang berisi operator penugasan shell atau evaluasi ekspresi
        for part in parts[1:]:
            if any(char in part for char in ['=', '$', '(', ')']):
                print(f"🚨 Guardrail Pemicu: Menemukan ekspresi shell terlarang '{part}'")
                return False
    except Exception as e:
        print(f"🚨 Gagal parse dengan shlex: {e}")
        return False
        
    return True


# ==========================================
# 🤖 INTEGRASI OLLAMA (LOKAL AI ENGINE)
# ==========================================

def ask_ollama(prompt: str, system_prompt: str = "") -> str:
    """
    Mengirimkan prompt ke local Ollama model qwen2.5-coder:7b.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0  # Menjaga determinisme perintah Docker
        }
    }
    if system_prompt:
        payload["system"] = system_prompt
        
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ Kesalahan Koneksi Ollama API: {e}")
        return "ERROR_OLLAMA_CONNECTION"


def ask_ollama_for_summary(logs: str, name: str, exit_code: str) -> str:
    """
    Meminta Ollama merangkum log kesalahan container ke dalam 1-2 kalimat bahasa Indonesia.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    system_prompt = (
        "Anda adalah DevOps Assistant. Anda menerima cuplikan log dari container Docker yang baru saja mati/error. "
        "Tugas Anda adalah menganalisis penyebab error tersebut secara singkat dan jelas dalam bahasa Indonesia (1-2 kalimat). "
        "Fokus pada akar masalah (root cause) tanpa detail teknis yang membingungkan. Jika log kosong, jelaskan bahwa container mati dengan exit code tersebut."
    )
    prompt = f"Container Name: {name}\nExit Code: {exit_code}\nLogs:\n{logs}"
    
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️ Gagal merangkum log menggunakan Ollama: {e}")
        return f"Container terhenti secara tidak terduga dengan Exit Code: {exit_code}. Gagal merangkum log secara otomatis."


def explain_output_ollama(command: str, output: str) -> str:
    """
    Meminta Ollama menjelaskan hasil output perintah Docker CLI dengan bahasa manusia yang ramah.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    system_prompt = (
        "Anda adalah DevOps Assistant lokal yang sangat ramah dan ahli. Anda menerima perintah Docker CLI yang dijalankan beserta hasil keluarannya (stdout).\n"
        "Tugas Anda adalah menjelaskan hasil tersebut ke dalam Bahasa Indonesia yang santun, ringkas, dan mudah dipahami oleh pemula sekalipun.\n"
        "Jangan menggunakan tabel markdown. Jelaskan secara naratif atau dengan poin-poin sederhana yang sangat manusiawi.\n"
        "Contoh: Jika output 'docker ps' kosong, jelaskan bahwa tidak ada container yang berjalan saat ini.\n"
        "Gunakan sapaan hangat dan batasi penjelasan maksimal 3 kalimat."
    )
    prompt = f"Command: {command}\nOutput:\n{output}"
    
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️ Gagal menjelaskan output dengan Ollama: {e}")
        return "Perintah berhasil dieksekusi secara lokal."


def explain_error_ollama(command: str, error: str) -> str:
    """
    Meminta Ollama menjelaskan pesan kesalahan (stderr) dengan bahasa manusia yang mudah dipahami.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    system_prompt = (
        "Anda adalah DevOps Assistant. Anda menerima perintah Docker CLI yang gagal beserta pesan error-nya (stderr).\n"
        "Tugas Anda adalah menjelaskan penyebab kegagalan tersebut dalam bahasa Indonesia yang ringkas dan mudah dipahami (maksimal 2 kalimat).\n"
        "Berikan saran perbaikan yang bersahabat."
    )
    prompt = f"Command: {command}\nError:\n{error}"
    
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️ Gagal menjelaskan error dengan Ollama: {e}")
        return "Terjadi kesalahan saat mengeksekusi perintah Docker."



# ==========================================
# 🐳 ASYNC DOCKER EVENT MONITOR (ARAH B)
# ==========================================

def monitor_docker_events():
    """
    Thread daemon untuk memantau event docker (die, oom) menggunakan Docker Python SDK.
    Mengirimkan alert log dengan ringkasan AI & Inline Keyboard Buttons.
    """
    while True:
        try:
            client = docker.from_env()
            print("🐳 Docker Event Monitor aktif dan memantau container...")
            
            # Memfilter event tipe container untuk aksi 'die' dan 'oom'
            for event in client.events(decode=True, filters={'type': 'container', 'event': ['die', 'oom']}):
                actor = event.get("Actor", {})
                attributes = actor.get("Attributes", {})
                container_name = attributes.get("name", "unknown")
                exit_code = attributes.get("exitCode", "unknown")
                action = event.get("Action", "die")
                
                print(f"🔔 [DOCKER EVENT] Container: {container_name} | Action: {action} | Exit Code: {exit_code}")
                
                # Jika tidak ada ALERT_CHAT_ID, lewati pengiriman Telegram tetapi cetak di server log
                if not ALERT_CHAT_ID:
                    continue
                
                # Ambil log kesalahan container (15 baris terakhir)
                try:
                    container = client.containers.get(container_name)
                    logs_bytes = container.logs(tail=15, stdout=True, stderr=True)
                    logs_content = logs_bytes.decode('utf-8', errors='ignore')
                except Exception as ex:
                    logs_content = f"(Tidak bisa mengambil log: {str(ex)})"
                
                # Minta Ollama merangkum log kesalahan
                summary = ask_ollama_for_summary(logs_content, container_name, exit_code)
                
                # Siapkan Inline Keyboard Buttons
                from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("🔄 Restart Container", callback_data=f"restart:{container_name}"),
                    InlineKeyboardButton("📝 Lihat Log Singkat", callback_data=f"logs:{container_name}")
                )
                
                alert_text = (
                    f"⚠️ **ALERT: CONTAINER ERROR/MATI!**\n\n"
                    f"🐳 **Nama Container:** `{container_name}`\n"
                    f"⏹️ **Aksi/Status:** `{action.upper()}`\n"
                    f"🚫 **Exit Code:** `{exit_code}`\n\n"
                    f"🤖 **Analisis AI (Ollama):**\n_{summary}_\n"
                )
                
                try:
                    bot.send_message(
                        ALERT_CHAT_ID,
                        alert_text,
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                except Exception as te:
                    print(f"❌ Gagal mengirim alert Telegram: {te}")
                    
        except Exception as e:
            print(f"⚠️ Koneksi Docker SDK terputus: {e}. Mencoba menyambung ulang dalam 5 detik...")
            time.sleep(5)


# ==========================================
# 🔘 INTERACTIVE BUTTONS (CALLBACK HANDLER)
# ==========================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """
    Menangani penekanan tombol restart dan log secara interaktif dengan teks loading dinamis.
    """
    user_id = call.from_user.id
    
    # Validasi otorisasi
    if ALLOWED_IDS and user_id not in ALLOWED_IDS:
        bot.answer_callback_query(call.id, "❌ Akses ditolak untuk akun Anda.")
        return
        
    data = call.data
    if ":" not in data:
        bot.answer_callback_query(call.id, "❌ Payload tombol tidak valid.")
        return
        
    action, container_name = data.split(":", 1)
    
    # Validasi nama container untuk menghindari command injection lateral
    if not re.match(r"^[a-zA-Z0-9\-_]+$", container_name):
        bot.answer_callback_query(call.id, "⚠️ Nama container tidak aman.")
        return
        
    client = docker.from_env()
    
    if action == "restart":
        # Tampilkan status pemrosesan di chat
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⏳ Memproses restart container `{container_name}`..."
        )
        
        try:
            container = client.containers.get(container_name)
            container.restart()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ Container `{container_name}` Berhasil Dinyalakan Kembali!"
            )
        except docker.errors.NotFound:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"❌ Gagal: Container `{container_name}` tidak ditemukan."
            )
        except Exception as e:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"❌ Gagal merestart container `{container_name}`.\nError: `{str(e)}`"
            )
            
    elif action == "logs":
        # Jalankan toast alert singkat di atas chat Telegram
        bot.answer_callback_query(call.id, f"Mengambil log `{container_name}`...")
        
        try:
            container = client.containers.get(container_name)
            logs_bytes = container.logs(tail=25, stdout=True, stderr=True)
            logs_content = logs_bytes.decode('utf-8', errors='ignore')
            if not logs_content.strip():
                logs_content = "(Log kosong)"
                
            bot.send_message(
                chat_id=call.message.chat.id,
                text=f"📝 **Log Terakhir untuk `{container_name}` (25 Baris):**\n\n```\n{logs_content[:3500]}\n```",
                parse_mode="Markdown"
            )
        except docker.errors.NotFound:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=f"❌ Container `{container_name}` tidak ditemukan."
            )
        except Exception as e:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=f"❌ Gagal mengambil log container: `{str(e)}`"
            )


# ==========================================
# 💬 TELEGRAM CHAT COMMANDS (ARAH A)
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    Menampilkan panduan awal serta menampilkan Telegram ID milik user saat ini.
    """
    user_id = message.from_user.id
    welcome_text = (
        f"👋 **Halo! Selamat datang di ChatOps Docker Bot**\n\n"
        f"Sistem otomatisasi server ini terhubung secara aman dengan Ollama dan Docker Engine lokal.\n\n"
        f"🔑 **Informasi Akun Anda:**\n"
        f"• **Username:** @{message.from_user.username or 'tidak_ada'}\n"
        f"• **Telegram ID:** `{user_id}`\n\n"
        f"💡 _Catat ID Anda dan masukkan ke file `.env` pada variabel `ALLOWED_TELEGRAM_IDS` dan `ALERT_CHAT_ID` agar bot aktif seutuhnya._\n\n"
        f"📋 **Contoh Perintah:**\n"
        f"- _'tampilkan container yang aktif'_\n"
        f"- _'hentikan container app-web'_\n"
        f"- _'restart container database'_\n"
        f"- _'lihat 15 baris log container api'_\n"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


@bot.message_handler(func=lambda msg: True)
def handle_natural_language_command(message):
    """
    Menangani input teks bahasa alami, memproses via Ollama,
    memvalidasi command via Guardrail, dan mengeksekusi di subprocess lokal.
    """
    user_id = message.from_user.id
    
    # Validasi otorisasi user secara deterministik
    if ALLOWED_IDS and user_id not in ALLOWED_IDS:
        bot.reply_to(message, "❌ Anda tidak memiliki izin akses untuk mengontrol server ini.")
        return
        
    user_input = message.text
    
    # Muat skill system prompt dari file md
    skills_path = os.path.join(os.path.dirname(__file__), "skills", "docker_management.md")
    system_instruction = ""
    if os.path.exists(skills_path):
        try:
            with open(skills_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()
        except Exception as e:
            print(f"⚠️ Gagal memuat file skill: {e}")
            
    # Tampilkan teks loading proses awal
    status_msg = bot.reply_to(message, "⏳ Menganalisis instruksi Anda dengan Ollama...")
    
    # Kirim payload ke Ollama lokal
    ollama_response = ask_ollama(user_input, system_prompt=system_instruction)
    
    if ollama_response == "ERROR_OLLAMA_CONNECTION":
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="❌ **Gagal menghubungi Ollama lokal!**\n\nPastikan service Ollama telah dijalankan di server (`systemctl status ollama`)."
        )
        return
        
    # Cek apakah AI memblokir instruksi atau gagal di filter keamanan
    if ollama_response == "BLOCKED" or not is_command_safe(ollama_response):
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=(
                f"⚠️ **Akses Ditolak / Perintah Tidak Aman!**\n\n"
                f"AI menghasilkan perintah: `{ollama_response}`\n"
                f"Sistem mendeteksi adanya manipulasi shell, perintah di luar whitelist, "
                f"atau potensi bahaya. Eksekusi dibatalkan demi keamanan server."
            )
        )
        return
        
    # Perbarui pesan untuk memberi info eksekusi perintah
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=f"⏳ Menjalankan perintah: `{ollama_response}`..."
    )
    
    # Jalankan perintah Docker via subprocess shell=False demi mencegah shell injection
    try:
        args = shlex.split(ollama_response)
        process = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            timeout=30
        )
        
        stdout_output = process.stdout.strip()
        stderr_output = process.stderr.strip()
        
        if process.returncode == 0:
            if not stdout_output:
                stdout_output = "(Sukses, tidak ada keluaran log)"
            
            # Hubungi Ollama untuk ringkasan manusiawi
            explanation = explain_output_ollama(ollama_response, stdout_output)
            
            result_text = (
                f"🤖 **Analisis AI (Ollama):**\n{explanation}\n\n"
                f"🖥️ **Command:** `{ollama_response}`\n"
                f"📤 **Raw Output:**\n```\n{stdout_output[:3000]}\n```"
            )
        else:
            if not stderr_output:
                stderr_output = f"(Kode keluar error: {process.returncode})"
            
            # Hubungi Ollama untuk ringkasan error manusiawi
            explanation = explain_error_ollama(ollama_response, stderr_output)
            
            result_text = (
                f"❌ **Perintah Gagal!**\n\n"
                f"🤖 **Analisis AI (Ollama):**\n{explanation}\n\n"
                f"🖥️ **Command:** `{ollama_response}`\n"
                f"⚠️ **Error:**\n```\n{stderr_output[:3000]}\n```"
            )
            
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=result_text,
            parse_mode="Markdown"
        )
        
    except subprocess.TimeoutExpired:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"❌ **Timeout!**\n\nBatas waktu 30 detik terlampaui saat menjalankan perintah `{ollama_response}`."
        )
    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"❌ **Error Internal Server:**\n`{str(e)}`"
        )


# ==========================================
# 🏁 RUN ENGINE
# ==========================================

if __name__ == "__main__":
    print("✨ Memulai ChatOps Engine...")
    
    # Jalankan background thread untuk monitoring Docker Events
    event_thread = threading.Thread(target=monitor_docker_events, daemon=True)
    event_thread.start()
    
    # Jalankan polling Telegram Bot (Long polling)
    try:
        print("🤖 Telegram Bot sedang mendengarkan pesan (Polling)...")
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except KeyboardInterrupt:
        print("\n👋 Mematikan ChatOps Engine...")
        sys.exit(0)
