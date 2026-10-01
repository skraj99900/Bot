import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
import subprocess
import os
import sys
import psutil
import json
import time
import threading
import zipfile
import re
import signal
import shlex
import traceback

# ----------------- ENVIRONMENT VARIABLES -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID_ENV = os.getenv("OWNER_ID")

if not BOT_TOKEN:
    sys.exit("[CRITICAL ERROR] 'BOT_TOKEN' environment variable is missing! Please configure it in Railway.")

if not OWNER_ID_ENV:
    sys.exit("[CRITICAL ERROR] 'OWNER_ID' environment variable is missing! Please configure it in Railway.")

try:
    OWNER_ID = int(OWNER_ID_ENV)
except ValueError:
    sys.exit("[CRITICAL ERROR] 'OWNER_ID' must be a valid integer Telegram user ID!")


# ----------------- ERROR-PROOF BOT SETUP -----------------
class SafeExceptionHandler(telebot.ExceptionHandler):
    """Handler ke andar koi bhi error aaye to bot crash/spam na kare, sirf log kare."""
    def handle(self, exception):
        print(f"[!] Handler error: {type(exception).__name__}: {exception}")
        traceback.print_exc()
        return True


bot = telebot.TeleBot(BOT_TOKEN, exception_handler=SafeExceptionHandler())


def _make_safe(fn):
    """
    Telegram ke common harmless errors ko handle karta hai:
      - "message is not modified"      -> ignore
      - "can't parse entities"         -> plain text me dubara bhejo
      - "query is too old / invalid"   -> ignore
    """
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiTelegramException as e:
            msg = str(e)
            if "message is not modified" in msg:
                return None
            if "query is too old" in msg or "query ID is invalid" in msg:
                return None
            if "can't parse entities" in msg and kwargs.get("parse_mode"):
                kwargs["parse_mode"] = None
                try:
                    return fn(*args, **kwargs)
                except ApiTelegramException as e2:
                    if "message is not modified" in str(e2):
                        return None
                    raise
            raise
    return inner


for _name in ("send_message", "edit_message_text", "edit_message_reply_markup",
              "send_document", "answer_callback_query"):
    setattr(bot, _name, _make_safe(getattr(bot, _name)))

# ----------------- PATHS / STORAGE -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Railway Volume use karna ho to Variables me DATA_DIR=/data set karo (files redeploy pe bachengi)
DATA_DIR = os.getenv("DATA_DIR") or BASE_DIR
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "allowed_users.json")
CONFIG_FILE = os.path.join(DATA_DIR, "bot_config.json")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
WORK_DIR = os.getenv("WORK_DIR") or os.path.join(DATA_DIR, "hosted")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

MAX_CHANNELS = 10
QUICK_WAIT = 20  # seconds: itne time tak command inline output dega, uske baad background me chala jayega

current_dir = WORK_DIR  # user ki scripts yahin upload hongi (bot ki apni files se alag)
bg_processes = {}
engine_logs = {}                     # pid -> log file path (finished engines ke logs bhi milenge)
waiting_for_channel_forward = set()  # Owner state waiting for channel forward
pending_requests = set()             # User IDs with active approval request sent to admin

START_TIME = time.time()

# ----------------- PROCESS / ENGINE HELPERS (NONSTOP SUPERVISOR) -----------------

SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
LOG_MAX_BYTES = 20 * 1024 * 1024
engines_lock = threading.RLock()
_next_sid = [1]

def child_env():
    """Hosted scripts ke liye environment. Bot ka token un tak nahi jata."""
    env = os.environ.copy()
    for k in ("BOT_TOKEN", "OWNER_ID"):
        env.pop(k, None)
    env["PYTHONUNBUFFERED"] = "1"            # logs turant dikhein
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"   # 'externally-managed-environment' error fix
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_ROOT_USER_ACTION"] = "ignore"
    return env

def normalize_cmd(cmd):
    """python / pip ko bot wale same Python se chalata hai (taaki 'command not found' na aaye)."""
    py = shlex.quote(sys.executable)
    cmd = re.sub(r'(^|&&\s*|;\s*|\|\|\s*)(python3?(?:\.\d+)?)(?=\s|$)',
                 lambda m: m.group(1) + py, cmd)
    cmd = re.sub(r'(^|&&\s*|;\s*|\|\|\s*)(pip3?)(?=\s|$)',
                 lambda m: m.group(1) + py + " -m pip", cmd)
    return cmd

def is_python_cmd(cmd):
    return bool(re.search(r'(^|&&|;)\s*python3?(\.\d+)?(\s|$)', cmd))

def read_log(path, limit=200000):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - limit))
            return f.read().decode("utf-8", errors="replace")
    except Exception:
        return ""

def fmt_code(text, max_len=3500):
    text = text.strip()
    if len(text) > max_len:
        text = "...\n" + text[-max_len:]
    return "```\n" + text.replace("```", "'" * 3) + "\n```"

def fmt_dur(sec):
    sec = int(sec)
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m, s_ = divmod(r, 60)
    if d: return f"{d}d {h}h"
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s_}s"
    return f"{s_}s"

def save_services():
    """Nonstop scripts ki list disk par save hoti hai, taaki bot restart/redeploy par wapas chalu ho."""
    with engines_lock:
        data = [
            {"id": i['id'], "cmd": i['cmd'], "cwd": i['cwd'], "chat_id": i.get('chat_id')}
            for i in bg_processes.values() if i.get('supervised') and not i.get('stopped')
        ]
        try:
            tmp = SERVICES_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, SERVICES_FILE)
        except Exception as e:
            print(f"[!] save_services error: {e}")

def _spawn(info):
    log_f = open(info['log'], "ab")
    try:
        try:
            if os.path.getsize(info['log']) > LOG_MAX_BYTES:
                log_f.truncate(0)
        except Exception:
            pass
        if info['restarts']:
            log_f.write(f"\n--- restart #{info['restarts']} @ {time.strftime('%H:%M:%S')} ---\n".encode())
            log_f.flush()
        proc = subprocess.Popen(
            normalize_cmd(info['cmd']), shell=True, cwd=info['cwd'],
            stdout=log_f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            env=child_env(), start_new_session=True
        )
    finally:
        log_f.close()
    info['process'] = proc
    info['started'] = time.time()
    return proc

def _supervise(info):
    """Script ruke/crash ho to khud dobara start karta hai. Crash-loop me backoff (3s -> 120s)."""
    fast = 0
    last_note = 0
    while not info.get('stopped'):
        try:
            proc = info['process']
            code = proc.wait()
            if info.get('stopped'):
                return
            ran = time.time() - info['started']
            fast = 0 if ran > 60 else fast + 1
            info['restarts'] += 1
            delay = 3 if fast <= 1 else min(5 * 2 ** (fast - 2), 120)

            now = time.time()
            if info.get('chat_id') and ((fast <= 3 and now - last_note > 20) or now - last_note > 600):
                last_note = now
                tail = read_log(info['log'], 3000)
                text = (f"🔁 *[AUTO-RESTART]* ID `{info['id']}`\n"
                        f"Script band ho gayi (exit `{code}`). `{delay}s` me dobara start ho rahi hai.\n")
                if tail.strip():
                    text += f"\n📜 *Last logs:*\n{fmt_code(tail, 2500)}"
                try:
                    bot.send_message(info['chat_id'], text, parse_mode="Markdown")
                except Exception as e:
                    print(f"[!] restart notify failed: {e}")

            for _ in range(delay):
                if info.get('stopped'):
                    return
                time.sleep(1)
            if info.get('stopped'):
                return
            _spawn(info)
        except Exception as e:
            print(f"[!] supervisor error (ID {info.get('id')}): {type(e).__name__}: {e}")
            time.sleep(15)

def make_supervised(info):
    info['supervised'] = True
    save_services()
    threading.Thread(target=_supervise, args=(info,), daemon=True).start()

def start_engine(cmd, chat_id=None, supervised=False, sid=None, cwd=None):
    """Command start karta hai. supervised=True -> nonstop (auto-restart + redeploy ke baad bhi)."""
    with engines_lock:
        if sid is None:
            sid = _next_sid[0]
        _next_sid[0] = max(_next_sid[0], sid) + 1
    if supervised:
        log_path = os.path.join(LOGS_DIR, f"service_{sid}.log")
    else:
        log_path = os.path.join(LOGS_DIR, f"engine_{sid}_{int(time.time())}.log")
    info = {'id': sid, 'cmd': cmd, 'cwd': cwd or current_dir, 'chat_id': chat_id,
            'supervised': False, 'stopped': False, 'restarts': 0,
            'log': log_path, 'process': None, 'started': 0}
    _spawn(info)
    bg_processes[sid] = info
    engine_logs[sid] = log_path
    if supervised:
        make_supervised(info)
    return info

def kill_proc(sid, restart=False):
    """Poora process group band karta hai (shell + uska child python script).
    restart=True -> sirf process maaro, supervisor use dobara chalu kar dega."""
    info = bg_processes.get(sid)
    if not info:
        return False
    if not restart:
        info['stopped'] = True
    proc = info['process']
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=3)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    if not restart:
        bg_processes.pop(sid, None)
        save_services()
    return True

def notify_when_done(info, chat_id):
    """(Non-nonstop commands ke liye) khatam hone par chat me log ke saath batata hai."""
    try:
        proc = info['process']
        code = proc.wait()
        if info.get('stopped') or info.get('supervised'):
            return
        bg_processes.pop(info['id'], None)
        tail = read_log(info['log'], 4000)
        status = "✅ *[ENGINE FINISHED]*" if code == 0 else "💥 *[ENGINE STOPPED / CRASHED]*"
        text = f"{status}\n*ID:* `{info['id']}` | *Exit code:* `{code}`\n"
        if tail.strip():
            text += f"\n📜 *Last logs:*\n{fmt_code(tail, 3000)}"
        bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception as e:
        print(f"[!] notify_when_done error: {e}")

def render_engines(with_back=False):
    if not bg_processes:
        return None, None
    text = "📊 *[ACTIVE ENGINES]*\n*════════════════*\n"
    markup = types.InlineKeyboardMarkup()
    for sid, info in sorted(bg_processes.items()):
        proc = info['process']
        alive = proc is not None and proc.poll() is None
        if info.get('supervised'):
            tag = "🟢 nonstop" if alive else "🔄 restarting"
        else:
            tag = "🟢 running" if alive else "⚪️ done"
        text += (f"⚙️ *ID:* `{sid}` | {tag} | ↻{info['restarts']} | up {fmt_dur(time.time() - info['started'])}\n"
                 f"   `{info['cmd'][:60]}`\n")
        markup.add(types.InlineKeyboardButton(f"🛑 Stop ID {sid}", callback_data=f"kill_{sid}"))
    if with_back:
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="btn_main_menu"))
    return text, markup

def restore_services():
    """Bot start hote hi pichhli nonstop scripts wapas chalu karta hai."""
    if not os.path.exists(SERVICES_FILE):
        return
    try:
        with open(SERVICES_FILE) as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] services.json read error: {e}")
        return
    ok, missing = 0, 0
    for sv in data:
        sid = sv.get('id', 0)
        _next_sid[0] = max(_next_sid[0], sid + 1)
        if not os.path.isdir(sv.get('cwd', '')):
            missing += 1
            continue
        try:
            start_engine(sv['cmd'], sv.get('chat_id'), True, sid, sv['cwd'])
            ok += 1
        except Exception as e:
            print(f"[!] restore failed for ID {sid}: {e}")
            missing += 1
    save_services()
    if ok or missing:
        text = f"♻️ *[SK HOST RESTARTED]*\n`{ok}` nonstop script(s) dobara start ho gayi."
        if missing:
            text += (f"\n⚠️ `{missing}` script ki files nahi mili (redeploy me delete ho gayi).\n"
                     f"Railway me Volume lagao + `DATA_DIR=/data` set karo, tab files bachengi.")
        try:
            bot.send_message(OWNER_ID, text, parse_mode="Markdown")
        except Exception as e:
            print(f"[!] restore notify failed: {e}")

def _janitor():
    """Logs ko bada hone se rokta hai (disk full na ho) aur purane logs hatata hai."""
    while True:
        time.sleep(300)
        try:
            active = set()
            for info in list(bg_processes.values()):
                active.add(info['log'])
                try:
                    if os.path.getsize(info['log']) > LOG_MAX_BYTES:
                        os.truncate(info['log'], 0)
                except Exception:
                    pass
            for fn in os.listdir(LOGS_DIR):
                p = os.path.join(LOGS_DIR, fn)
                if fn.startswith("engine_") and p not in active and time.time() - os.path.getmtime(p) > 86400:
                    os.remove(p)
        except Exception as e:
            print(f"[!] janitor error: {e}")

threading.Thread(target=_janitor, daemon=True).start()

# ----------------- ESCAPE / SANITIZATION HELPERS -----------------

def escape_markdown(text):
    """
    Escapes Telegram legacy Markdown special characters (*, _, `, [).
    Prevents 'can't parse entities' errors when usernames or names contain symbols.
    """
    if not text:
        return ""
    chars = ['*', '_', '`', '[']
    for ch in chars:
        text = text.replace(ch, f"\\{ch}")
    return text

# ----------------- STORAGE HELPERS -----------------

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return {OWNER_ID}
    return {OWNER_ID}

def save_users(users_set):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users_set), f)

def load_config():
    default_config = {"required_channels": []}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "required_channel_id" in data and data["required_channel_id"]:
                    data["required_channels"] = [{
                        "id": data["required_channel_id"],
                        "title": data.get("required_channel_title") or "Required Channel",
                        "username": data.get("required_channel_username"),
                        "invite_link": data.get("required_channel_invite_link")
                    }]
                if "required_channels" not in data:
                    data["required_channels"] = []
                return data
        except Exception:
            return default_config
    return default_config

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

allowed_users = load_users()
bot_config = load_config()

# ----------------- VERIFICATION HELPERS -----------------

def is_owner(user_id):
    return user_id == OWNER_ID

def is_allowed_user(user_id):
    return user_id in allowed_users or user_id == OWNER_ID

def check_channel_subscriptions(user_id):
    """
    Checks if a user is subscribed to ALL configured channels (up to 10).
    Returns: (is_all_joined: bool, missing_channels: list of dicts)
    """
    if is_owner(user_id):
        return True, []

    channels = bot_config.get("required_channels", [])
    if not channels:
        return True, []

    missing = []
    for ch in channels:
        ch_id = ch.get("id")
        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                missing.append(ch)
        except Exception as e:
            print(f"[!] Error checking channel {ch_id}: {e}")
            missing.append(ch)

    return (len(missing) == 0), missing

def get_join_channels_keyboard(missing_channels):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, ch in enumerate(missing_channels, 1):
        link = ch.get("invite_link")
        title = ch.get("title", f"Channel {i}")
        if link:
            markup.add(types.InlineKeyboardButton(f"📢 Join {title}", url=link))
    markup.add(types.InlineKeyboardButton("🔄 Verify Membership", callback_data="verify_membership"))
    return markup

def get_uptime():
    uptime_seconds = int(time.time() - START_TIME)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    return f"{days}d {hours}h {minutes}m {seconds}s"

# ----------------- UI / KEYBOARDS -----------------

def get_main_menu_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_status = types.InlineKeyboardButton("⏳ Status", callback_data="btn_status")
    btn_vitals = types.InlineKeyboardButton("🧬 Vitals", callback_data="btn_sysinfo")
    btn_ram = types.InlineKeyboardButton("🧠 RAM", callback_data="btn_memory")
    btn_disk = types.InlineKeyboardButton("💽 Disk", callback_data="btn_disk")
    btn_ps = types.InlineKeyboardButton("⚙️ Engines (PS)", callback_data="btn_ps")
    btn_myid = types.InlineKeyboardButton("🪪 My ID", callback_data="btn_myid")
    btn_help = types.InlineKeyboardButton("📖 Help Guide", callback_data="btn_help")

    markup.add(btn_status, btn_vitals)
    markup.add(btn_ram, btn_disk)
    markup.add(btn_ps, btn_myid)

    if is_owner(user_id):
        btn_channel = types.InlineKeyboardButton("📢 Channel Manager", callback_data="btn_channel_info")
        btn_users = types.InlineKeyboardButton("👥 Users List", callback_data="btn_list_users")
        markup.add(btn_channel, btn_users)

    markup.add(btn_help)
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="btn_main_menu"))
    return markup

def get_help_text():
    channels = bot_config.get("required_channels", [])
    count = len(channels)
    return f"""⚡️ *SK HOST | NEON TERMINAL* ⚡️
*═════════════════════════*
Welcome to the core system. You have full terminal access. 🚀

💻 *TERMINAL ACTIONS:*
▪️ Direct commands (`ls`, `mkdir`, `git status`)
▪️ `cd <dir>` - Switch active directory 📂
▪️ `pip install <pkg>` - Install Python package 💉
▪️ `python <script.py>` - Execute scripts 🔥
▪️ Python script 20s se zyada chale to *NONSTOP mode* me chali jati hai ♻️

🗂 *FILE OPERATIONS:*
▪️ Send document directly to bot - Uploads to active dir 📤
▪️ `/download <filename>` - Download file from server 📥
▪️ `/unzip <file.zip>` - Zip extract karo 📦

⚙️ *BACKGROUND ENGINES:*
▪️ `/run <cmd>` - Nonstop engine (auto-restart) 🟢
▪️ `/stop <id>` - Engine band karo 🛑
▪️ `/restart <id>` - Engine restart karo 🔁
▪️ `/ps` - List all active engines 📊
▪️ `/logs <id>` - Engine ke logs dekho 📜

🖥 *SYSTEM VITALS:*
▪️ `/status` - Live uptime & overview ⏳
▪️ `/sysinfo` - CPU & RAM utilization 🧬
▪️ `/disk` - Storage details 💽
▪️ `/memory` - RAM usage breakdown 🧠

🔑 *ACCESS & CONTROL:*
▪️ `/myid` - View your Telegram User ID 🪪
▪️ `/menu` or `/start` - Interactive Dashboard 🎛
▪️ `/channel` - Add channel via forward *(Max 10)* 📢
▪️ `/channels` - View & remove channels *(Owner only)* 📋
▪️ `/channel_del <id>` - Remove specific channel ❌
▪️ `/add <id>` & `/remove <id>` - Whitelist access 👥

🔒 *Active Channels:* `{count} / {MAX_CHANNELS}`
*═════════════════════════*
*SYSTEM READY >_* Type a command or use the buttons below:"""

# ----------------- OWNER CHANNEL MANAGEMENT -----------------

@bot.message_handler(commands=['channel'])
def set_channel_prompt(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "💀 *[ACCESS DENIED]* Privilege escalation failed. Owner only.", parse_mode="Markdown")
        return
    
    current_count = len(bot_config.get("required_channels", []))
    if current_count >= MAX_CHANNELS:
        bot.reply_to(
            message,
            f"⚠️ *[LIMIT REACHED]* You already have `{MAX_CHANNELS}` channels added!\n"
            f"Use `/channels` or `/channel_del <id>` to remove one first.",
            parse_mode="Markdown"
        )
        return

    waiting_for_channel_forward.add(message.from_user.id)
    text = (
        f"📢 *[CHANNEL SETUP MODE]* ({current_count}/{MAX_CHANNELS} active)\n\n"
        f"1. Make sure you add this bot as an **Administrator** in your channel with invite link permissions.\n"
        f"2. **Forward any post/message from that channel to this chat right now.**\n\n"
        f"Send `/cancel` at any time to cancel."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Cancel Setup", callback_data="cancel_channel_setup"))
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['channels'])
def list_channels_cmd(message):
    if not is_owner(message.from_user.id): return
    show_channel_manager(message.chat.id, None)

@bot.message_handler(commands=['channel_del'])
def delete_channel_by_arg(message):
    if not is_owner(message.from_user.id): return
    args = message.text.split(" ")
    if len(args) < 2:
        bot.reply_to(message, "⚠️ *Format Error:*\nUse `/channel_del <channel_id>` or `/channels` to manage with buttons.", parse_mode="Markdown")
        return
    try:
        del_id = int(args[1])
        channels = bot_config.get("required_channels", [])
        before = len(channels)
        bot_config["required_channels"] = [c for c in channels if c.get("id") != del_id]
        if len(bot_config["required_channels"]) < before:
            save_config(bot_config)
            bot.reply_to(message, f"✅ Removed channel `{del_id}`.", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Channel ID `{del_id}` not found in list.", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "⚠️ Channel ID must be a numeric integer.")

def show_channel_manager(chat_id, message_id=None):
    channels = bot_config.get("required_channels", [])
    markup = types.InlineKeyboardMarkup(row_width=1)

    if not channels:
        text = "📢 *[CHANNEL MANAGER]*\n\nNo required channels configured yet (0/10).\nSend `/channel` to add one!"
    else:
        text = f"📢 *[CHANNEL MANAGER]* ({len(channels)}/{MAX_CHANNELS} Active)\n\n"
        for i, ch in enumerate(channels, 1):
            clean_title = escape_markdown(ch.get('title', 'Channel'))
            text += f"{i}. *{clean_title}*\n   ID: `{ch.get('id')}`\n   Link: {ch.get('invite_link') or 'None'}\n\n"
            markup.add(types.InlineKeyboardButton(f"🗑 Remove: {ch.get('title', 'Channel')[:25]}", callback_data=f"del_ch_{ch.get('id')}"))

    if len(channels) < MAX_CHANNELS:
        markup.add(types.InlineKeyboardButton("➕ Add New Channel", callback_data="add_new_channel_btn"))
    markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="btn_main_menu"))

    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    if message.from_user.id in waiting_for_channel_forward:
        waiting_for_channel_forward.remove(message.from_user.id)
        bot.reply_to(message, "❌ Setup cancelled.")

@bot.message_handler(commands=['add'])
def add_user(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "💀 *[ACCESS DENIED]* Owner only.", parse_mode="Markdown")
        return
    try:
        new_id = int(message.text.split(" ")[1])
        allowed_users.add(new_id)
        save_users(allowed_users)
        bot.reply_to(message, f"⚡️ *[ACCESS GRANTED]*\nUser `{new_id}` added to authorized list! 🚀", parse_mode="Markdown")
        try:
            bot.send_message(new_id, "🎉 *[ACCESS APPROVED]*\nThe Admin has approved your terminal access! Type /start to begin.", parse_mode="Markdown")
        except Exception:
            pass
    except Exception:
        bot.reply_to(message, "⚠️ *Format Error:*\nUse: `/add <userid>`", parse_mode="Markdown")

@bot.message_handler(commands=['remove'])
def remove_user(message):
    if not is_owner(message.from_user.id): return
    try:
        del_id = int(message.text.split(" ")[1])
        if del_id == OWNER_ID:
            bot.reply_to(message, "👑 *[SYSTEM ERROR]* Cannot disconnect the master owner! 🧠", parse_mode="Markdown")
            return
        if del_id in allowed_users:
            allowed_users.remove(del_id)
            save_users(allowed_users)
            bot.reply_to(message, f"🗑 *[USER REMOVED]*\nUser `{del_id}` removed from authorized list! 🔌", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ User ID not found in whitelist.")
    except Exception:
        bot.reply_to(message, "⚠️ *Format Error:*\nUse: `/remove <userid>`", parse_mode="Markdown")

# ----------------- CHANNEL FORWARD CAPTURE (UP TO 10) -----------------

@bot.message_handler(func=lambda msg: msg.from_user.id in waiting_for_channel_forward and msg.forward_from_chat is not None)
def handle_channel_forward(message):
    user_id = message.from_user.id
    chat = message.forward_from_chat
    waiting_for_channel_forward.discard(user_id)

    if chat.type != 'channel':
        bot.reply_to(message, "❌ The forwarded message must be from a **Channel**. Setup cancelled.", parse_mode="Markdown")
        return

    channels = bot_config.get("required_channels", [])
    if len(channels) >= MAX_CHANNELS:
        bot.reply_to(message, f"⚠️ Maximum limit of {MAX_CHANNELS} channels reached. Remove one first using `/channels`.", parse_mode="Markdown")
        return

    channel_id = chat.id
    channel_title = chat.title or "Required Channel"
    channel_username = chat.username

    if any(c.get("id") == channel_id for c in channels):
        bot.reply_to(message, f"⚠️ Channel *{escape_markdown(channel_title)}* (`{channel_id}`) is already in your required list!", parse_mode="Markdown")
        return

    invite_link = None
    try:
        chat_info = bot.get_chat(channel_id)
        if chat_info.invite_link:
            invite_link = chat_info.invite_link
        elif channel_username:
            invite_link = f"https://t.me/{channel_username}"
        else:
            link_obj = bot.create_chat_invite_link(channel_id)
            invite_link = link_obj.invite_link
    except Exception as e:
        if channel_username:
            invite_link = f"https://t.me/{channel_username}"
        print(f"[!] Could not create or fetch invite link: {e}")

    new_channel = {
        "id": channel_id,
        "title": channel_title,
        "username": channel_username,
        "invite_link": invite_link
    }
    channels.append(new_channel)
    bot_config["required_channels"] = channels
    save_config(bot_config)

    clean_title = escape_markdown(channel_title)
    success_text = (
        f"✅ *[CHANNEL #{len(channels)} ADDED SUCCESSFULLY]*\n\n"
        f"📌 *Title:* {clean_title}\n"
        f"🆔 *Channel ID:* `{channel_id}`\n"
        f"🔗 *Link:* {invite_link or 'No link generated'}\n\n"
        f"Total Active Channels: `{len(channels)}/{MAX_CHANNELS}`\n"
        f"Users must now join all active channels before accessing the bot!"
    )
    bot.reply_to(message, success_text, parse_mode="Markdown")

# ----------------- GENERAL & DASHBOARD COMMANDS -----------------

@bot.message_handler(commands=['start', 'help', 'menu', 'commands'])
def send_menu(message):
    user_id = message.from_user.id

    if is_owner(user_id):
        text = get_help_text()
        bot.reply_to(message, text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))
        return

    # Check All Channel Memberships
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(
            message,
            f"⚠️ *[MEMBERSHIP REQUIRED]*\nYou must join all `{len(missing)}` pending channel(s) below to access this terminal.",
            parse_mode="Markdown",
            reply_markup=get_join_channels_keyboard(missing)
        )
        return

    # If all joined, check Whitelist Authorization
    if not is_allowed_user(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 Request Authorization from Admin", callback_data="send_auth_request"))
        bot.reply_to(
            message,
            "✅ *[CHANNELS VERIFIED]*\nYou are a member of all required channels.\n\n"
            "🔒 *[AUTHORIZATION REQUIRED]*\nYour account is not whitelisted by the Admin yet.\n"
            "Click below to send an authorization request to the Admin.",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

    text = get_help_text()
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(user_id))

@bot.message_handler(commands=['myid'])
def my_id(message):
    bot.reply_to(message, f"🪪 *YOUR TELEGRAM ID:* `{message.from_user.id}` ⚡️", parse_mode="Markdown")

# ----------------- SYSTEM INFO / VITALS -----------------

@bot.message_handler(commands=['status'])
def server_status(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    uptime = get_uptime()
    bot.reply_to(
        message,
        f"🟢 *SERVER STATUS:* `ONLINE`\n⏳ *RUNTIME:* `{uptime}`\n⚙️ *ACTIVE ENGINES:* `{len(bg_processes)}`\n⚡️ *CONNECTION:* `SECURE`",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(user_id)
    )

@bot.message_handler(commands=['sysinfo', 'disk', 'memory'])
def sys_info(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    if message.text == '/memory':
        mem = psutil.virtual_memory()
        bot.reply_to(message, f"🧠 *MEMORY CORE:*\n*Total:* `{mem.total / (1024**3):.2f} GB`\n*Used:* `{mem.used / (1024**3):.2f} GB` ({mem.percent}%) ⚡️", parse_mode="Markdown")
    elif message.text == '/disk':
        disk = psutil.disk_usage('/')
        bot.reply_to(message, f"💽 *STORAGE VAULT:*\n*Total:* `{disk.total / (1024**3):.2f} GB`\n*Used:* `{disk.used / (1024**3):.2f} GB` ({disk.percent}%) 📂", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"🧬 *SYSTEM VITALS:*\n*CPU Usage:* `{psutil.cpu_percent()}%` 🔥\n*RAM Usage:* `{psutil.virtual_memory().percent}%` 🧠", parse_mode="Markdown")

# ----------------- BACKGROUND ENGINES (RUN, PS, STOP) -----------------

@bot.message_handler(commands=['run'])
def run_bg(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    global current_dir
    cmd = message.text.replace('/run', '', 1).strip()
    if not cmd:
        bot.reply_to(message, "⚠️ *Format Error:*\nUse: `/run <command>` (e.g. `/run python app.py`)", parse_mode="Markdown")
        return

    try:
        info = start_engine(cmd, message.chat.id, supervised=True)
        bot.reply_to(
            message,
            f"🟢 *[NONSTOP ENGINE STARTED]*\n*ID:* `{info['id']}` ⚙️\n*CMD:* `{cmd}`\n\n"
            f"♻️ Crash ya redeploy hone par khud dobara chalu hoga.\n"
            f"📜 `/logs {info['id']}`  |  🔁 `/restart {info['id']}`  |  🛑 `/stop {info['id']}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ *[CRASH]* Engine failed: {e}")

@bot.message_handler(commands=['ps'])
def list_ps(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    text, markup = render_engines()
    if not text:
        bot.reply_to(message, "💤 *[SYSTEM IDLE]* No background engines running.", parse_mode="Markdown")
    else:
        bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['stop'])
def stop_ps(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    try:
        pid = int(message.text.split(" ")[1])
        if pid in bg_processes:
            kill_proc(pid)
            bot.reply_to(message, f"🛑 *[ENGINE KILLED]* ID `{pid}` band kar di gayi (ab auto-restart nahi hogi)! 💀", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ *[NOT FOUND]* Is ID ka koi engine nahi mila. `/ps` dekho.")
    except Exception:
        bot.reply_to(message, "⚠️ *Format Error:*\nUse: `/stop <id>`", parse_mode="Markdown")

@bot.message_handler(commands=['restart'])
def restart_engine(message):
    if not guard(message):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "⚠️ *Usage:* `/restart <id>`", parse_mode="Markdown")
        return
    sid = int(parts[1])
    info = bg_processes.get(sid)
    if not info or not info.get('supervised'):
        bot.reply_to(message, "❌ Is ID ka nonstop engine nahi mila. `/ps` dekho.")
        return
    kill_proc(sid, restart=True)
    bot.reply_to(message, f"🔁 ID `{sid}` restart ho rahi hai...", parse_mode="Markdown")

# ----------------- LOGS / UNZIP -----------------

def guard(message):
    """Authorization + channel check. True = aage badho."""
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return False
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return False
    return True

@bot.message_handler(commands=['logs'])
def show_logs(message):
    if not guard(message):
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "⚠️ *Usage:* `/logs <id>`  (ID `/ps` se milega)", parse_mode="Markdown")
        return
    pid = int(parts[1])
    path = engine_logs.get(pid)
    if not path or not os.path.exists(path):
        bot.reply_to(message, "❌ Is ID ka log nahi mila.")
        return
    text = read_log(path, 3500)
    running = pid in bg_processes and bg_processes[pid]['process'].poll() is None
    state = "🟢 running" if running else "⚪️ stopped"
    if not text.strip():
        bot.reply_to(message, f"📜 *ID* `{pid}` ({state})\nAbhi tak koi output nahi aaya.", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"📜 *LOGS — ID* `{pid}` ({state})\n{fmt_code(text)}", parse_mode="Markdown")

@bot.message_handler(commands=['unzip'])
def unzip_file(message):
    if not guard(message):
        return
    name = message.text.replace('/unzip', '', 1).strip()
    if not name:
        bot.reply_to(message, "⚠️ *Usage:* `/unzip <file.zip>`", parse_mode="Markdown")
        return
    path = os.path.join(current_dir, name)
    if not os.path.isfile(path) or not zipfile.is_zipfile(path):
        bot.reply_to(message, "❌ Zip file nahi mili (ya valid zip nahi hai).")
        return
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            z.extractall(current_dir)
        top = sorted({n.split('/')[0] for n in names if n.split('/')[0]})
        shown = "\n".join(f"▪️ {t}" for t in top[:15])
        more = f"\n...+{len(top) - 15} more" if len(top) > 15 else ""
        bot.reply_to(message, f"📦 [EXTRACTED] {len(names)} files\n\n{shown}{more}\n\nAb `cd <folder>` karke script chalao.")
    except Exception as e:
        bot.reply_to(message, f"❌ Unzip failed: {e}")

# ----------------- FILE OPERATIONS -----------------

@bot.message_handler(commands=['download'])
def download_file(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    global current_dir
    filename = message.text.replace('/download', '', 1).strip()
    if not filename:
        bot.reply_to(message, "⚠️ *Usage:* `/download <filename>`", parse_mode="Markdown")
        return

    filepath = os.path.join(current_dir, filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        bot.reply_to(message, "📥 *[EXTRACTING]* Transmitting file... ⏳", parse_mode="Markdown")
        try:
            with open(filepath, 'rb') as f:
                bot.send_document(message.chat.id, f)
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send file: {e}")
    else:
        bot.reply_to(message, "❌ *[404]* File not found in current directory! 🔍")

@bot.message_handler(content_types=['document'])
def handle_upload(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    global current_dir
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        safe_name = os.path.basename(message.document.file_name or f"file_{message.document.file_unique_id}")
        filepath = os.path.join(current_dir, safe_name)
        with open(filepath, 'wb') as new_file:
            new_file.write(downloaded_file)
        hint = ("\n\n📦 Zip hai? `/unzip " + safe_name + "` bhejo.") if safe_name.lower().endswith(".zip") else ""
        bot.reply_to(message, f"📤 *[UPLOAD COMPLETE]*\nFile secured at:\n`{filepath}` 🔒{hint}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *[UPLOAD FAILED]* Error: {e}")

# ----------------- DIRECT TERMINAL COMMANDS -----------------

@bot.message_handler(content_types=['text'], func=lambda message: bool(message.text) and not message.text.startswith('/'))
def direct_terminal(message):
    user_id = message.from_user.id
    if not is_allowed_user(user_id):
        bot.reply_to(message, "⛔️ *[UNAUTHORIZED]* Access restricted.", parse_mode="Markdown")
        return
    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.reply_to(message, "⚠️ *Access Denied:* Please join all channels.", reply_markup=get_join_channels_keyboard(missing), parse_mode="Markdown")
        return

    global current_dir
    cmd = message.text.strip()

    if cmd.startswith("cd "):
        new_dir = cmd[3:].strip()
        target_path = os.path.abspath(os.path.join(current_dir, new_dir))
        if os.path.exists(target_path) and os.path.isdir(target_path):
            current_dir = target_path
            bot.reply_to(message, f"📂 *[DIR CHANGED]*\nNow in:\n`{current_dir}` ⚡️", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ *[404]* Directory does not exist!")
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        info = start_engine(cmd, message.chat.id)
        proc = info['process']
        try:
            proc.wait(timeout=QUICK_WAIT)
        except subprocess.TimeoutExpired:
            if is_python_cmd(cmd):
                # Lambi chalne wali python script = host hui script -> NONSTOP mode
                make_supervised(info)
                bot.reply_to(
                    message,
                    f"🟢 *[HOSTED — NONSTOP MODE]*\n*ID:* `{info['id']}` ⚙️\n\n"
                    f"♻️ Ab ye script kabhi nahi rukegi: crash ya redeploy par khud dobara chalu hogi.\n"
                    f"📜 `/logs {info['id']}`  |  🔁 `/restart {info['id']}`  |  🛑 `/stop {info['id']}`\n\n"
                    f"_(Agar ye ek baar chalke khatam hone wali job hai to `/stop {info['id']}` kar dena.)_",
                    parse_mode="Markdown"
                )
            else:
                threading.Thread(target=notify_when_done, args=(info, message.chat.id), daemon=True).start()
                bot.reply_to(
                    message,
                    f"🟢 *[RUNNING IN BACKGROUND]*\n*ID:* `{info['id']}` ⚙️\n"
                    f"Command {QUICK_WAIT}s se zyada chal rahi hai.\n"
                    f"📜 `/logs {info['id']}`  |  🛑 `/stop {info['id']}`\nKhatam hone par yahin bata dunga.",
                    parse_mode="Markdown"
                )
            return

        bg_processes.pop(info['id'], None)
        result = read_log(info['log'])
        code = proc.returncode

        if not result.strip():
            if code == 0:
                bot.reply_to(message, "✅ *[EXECUTED]* Command succeeded with empty output. 🥷", parse_mode="Markdown")
            else:
                bot.reply_to(message, f"🛑 *[COMMAND ERROR]* Exit code `{code}` (no output)", parse_mode="Markdown")
        elif len(result) > 3800:
            with open(info['log'], "rb") as f:
                bot.send_document(message.chat.id, f, visible_file_name="output.txt",
                                  caption="⚠️ Output bahut bada hai, file me bheja.")
        else:
            head = "" if code == 0 else f"🛑 *[COMMAND ERROR]* (exit `{code}`)\n"
            bot.reply_to(message, head + fmt_code(result, 3800), parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *[SYSTEM ERROR]*: {e}")

# ----------------- INLINE CALLBACK HANDLERS -----------------

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        _handle_callbacks_impl(call)
    except Exception as e:
        print(f"[!] Callback error ({call.data}): {type(e).__name__}: {e}")
        try:
            bot.answer_callback_query(call.id, "⚠️ Kuch gadbad hui, dubara try karo.")
        except Exception:
            pass

def _handle_callbacks_impl(call):
    user_id = call.from_user.id

    # 1. Verification of Channel Subscriptions
    if call.data == "verify_membership":
        is_all_joined, missing = check_channel_subscriptions(user_id)
        if is_all_joined:
            if is_allowed_user(user_id):
                bot.answer_callback_query(call.id, "✅ Verified! Welcome back.")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=get_help_text(),
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
            else:
                bot.answer_callback_query(call.id, "✅ All channels verified!")
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📩 Request Authorization from Admin", callback_data="send_auth_request"))
                channels_count = len(bot_config.get("required_channels", []))
                text = (
                    f"🎉 *[CHANNELS VERIFICATION SUCCESS]*\n\n"
                    f"You have successfully joined all `{channels_count}` official channel(s)! 🚀\n\n"
                    f"⚠️ *Next Step:* Terminal access requires Administrator approval.\n"
                    f"Click below to send an authorization request to the Admin."
                )
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
        else:
            bot.answer_callback_query(call.id, f"❌ You still have {len(missing)} channel(s) left to join!", show_alert=True)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=get_join_channels_keyboard(missing)
            )
        return

    # 2. User Sends Auth Request to Admin (FIXED: Escaped characters & fallback)
    if call.data == "send_auth_request":
        is_all_joined, missing = check_channel_subscriptions(user_id)
        if not is_all_joined:
            bot.answer_callback_query(call.id, "❌ You must join all channels first!", show_alert=True)
            return

        if is_allowed_user(user_id):
            bot.answer_callback_query(call.id, "✅ You are already authorized!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=get_help_text(),
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return

        # Sanitize names to prevent Markdown parse error (byte offset issue)
        raw_full_name = f"{call.from_user.first_name} {call.from_user.last_name or ''}".strip()
        safe_full_name = escape_markdown(raw_full_name)
        
        if call.from_user.username:
            safe_username = "@" + escape_markdown(call.from_user.username)
        else:
            safe_username = "None"

        admin_markup = types.InlineKeyboardMarkup(row_width=2)
        btn_allow = types.InlineKeyboardButton("✅ Allow Access", callback_data=f"auth_allow_{user_id}")
        btn_deny = types.InlineKeyboardButton("❌ Deny Access", callback_data=f"auth_deny_{user_id}")
        admin_markup.add(btn_allow, btn_deny)

        channels_count = len(bot_config.get("required_channels", []))
        admin_text = (
            f"🔔 *[NEW ACCESS REQUEST]*\n\n"
            f"👤 *Name:* {safe_full_name}\n"
            f"🔗 *Username:* {safe_username}\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"📢 *Channels Status:* Verified Member of all `{channels_count}` channels ✅\n\n"
            f"Would you like to grant terminal access to this user?"
        )

        try:
            bot.send_message(OWNER_ID, admin_text, parse_mode="Markdown", reply_markup=admin_markup)
            pending_requests.add(user_id)
            bot.answer_callback_query(call.id, "📨 Request sent to Admin!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="⏳ *[REQUEST TRANSMITTED]*\n\nYour authorization request has been sent to the System Admin.\nYou will receive a notification as soon as it is approved! 🚀",
                parse_mode="Markdown"
            )
        except Exception as e:
            # Fallback to plain text if Markdown still encounters formatting conflicts
            try:
                plain_text = (
                    f"🔔 [NEW ACCESS REQUEST]\n\n"
                    f"Name: {raw_full_name}\n"
                    f"Username: @{call.from_user.username if call.from_user.username else 'None'}\n"
                    f"User ID: {user_id}\n"
                    f"Channels Status: Verified Member of all {channels_count} channels\n\n"
                    f"Would you like to grant terminal access to this user?"
                )
                bot.send_message(OWNER_ID, plain_text, reply_markup=admin_markup)
                pending_requests.add(user_id)
                bot.answer_callback_query(call.id, "📨 Request sent to Admin!")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="⏳ *[REQUEST TRANSMITTED]*\n\nYour authorization request has been sent to the System Admin.\nYou will receive a notification as soon as it is approved! 🚀",
                    parse_mode="Markdown"
                )
            except Exception as e2:
                bot.answer_callback_query(call.id, f"Error reaching Admin: {e2}", show_alert=True)
        return

    # 3. Admin Decision: ALLOW
    if call.data.startswith("auth_allow_"):
        if not is_owner(user_id):
            bot.answer_callback_query(call.id, "⛔ Owner only.", show_alert=True)
            return
        target_uid = int(call.data.replace("auth_allow_", ""))
        allowed_users.add(target_uid)
        save_users(allowed_users)
        pending_requests.discard(target_uid)

        bot.answer_callback_query(call.id, f"User {target_uid} approved!")
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + f"\n\n🟢 DECISION: Allowed by Admin on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception:
            pass

        try:
            user_markup = types.InlineKeyboardMarkup()
            user_markup.add(types.InlineKeyboardButton("🚀 Launch Terminal Dashboard", callback_data="btn_main_menu"))
            bot.send_message(
                target_uid,
                "🎉 *[ACCESS APPROVED]*\n\nThe System Admin has approved your request! You now have full terminal access.",
                parse_mode="Markdown",
                reply_markup=user_markup
            )
        except Exception as e:
            print(f"[!] Notification to user {target_uid} failed: {e}")
        return

    # 4. Admin Decision: DENY
    if call.data.startswith("auth_deny_"):
        if not is_owner(user_id):
            bot.answer_callback_query(call.id, "⛔ Owner only.", show_alert=True)
            return
        target_uid = int(call.data.replace("auth_deny_", ""))
        pending_requests.discard(target_uid)

        bot.answer_callback_query(call.id, f"User {target_uid} denied.")
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + f"\n\n🔴 DECISION: Denied by Admin on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception:
            pass

        try:
            bot.send_message(target_uid, "🚫 *[ACCESS DENIED]*\nThe System Admin has rejected your authorization request.", parse_mode="Markdown")
        except Exception:
            pass
        return

    # Channel Manager Actions
    if call.data == "btn_channel_info":
        if not is_owner(user_id): return
        show_channel_manager(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if call.data == "add_new_channel_btn":
        if not is_owner(user_id): return
        current_count = len(bot_config.get("required_channels", []))
        if current_count >= MAX_CHANNELS:
            bot.answer_callback_query(call.id, f"Limit reached ({MAX_CHANNELS} channels maximum).", show_alert=True)
            return
        waiting_for_channel_forward.add(user_id)
        text = (
            f"📢 *[ADD CHANNEL]* ({current_count}/{MAX_CHANNELS})\n\n"
            f"Make sure bot is admin in the channel.\n"
            f"Now **forward any message from that channel** here.\n\n"
            f"Send `/cancel` to cancel."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_channel_setup"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if call.data.startswith("del_ch_"):
        if not is_owner(user_id): return
        target_ch_id = int(call.data.replace("del_ch_", ""))
        channels = bot_config.get("required_channels", [])
        bot_config["required_channels"] = [c for c in channels if c.get("id") != target_ch_id]
        save_config(bot_config)
        bot.answer_callback_query(call.id, "Channel removed!")
        show_channel_manager(call.message.chat.id, call.message.message_id)
        return

    # Check authorization for other controls
    if not is_allowed_user(user_id):
        bot.answer_callback_query(call.id, "⛔ Access denied. Unauthorized.", show_alert=True)
        return

    is_all_joined, missing = check_channel_subscriptions(user_id)
    if not is_all_joined:
        bot.answer_callback_query(call.id, "⚠️ Channel membership required!", show_alert=True)
        return

    # Kill Process Callback
    if call.data.startswith("kill_"):
        pid = int(call.data.replace("kill_", ""))
        if pid in bg_processes:
            try:
                kill_proc(pid)
                bot.answer_callback_query(call.id, f"Engine {pid} killed!")
                bot.send_message(call.message.chat.id, f"🛑 *[ENGINE KILLED]* ID `{pid}` band kar di gayi.", parse_mode="Markdown")
            except Exception as e:
                bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "Already stopped ya ID nahi mila.")
        return

    # Dashboard Actions
    if call.data == "btn_main_menu":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=get_help_text(),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_status":
        uptime = get_uptime()
        text = (
            f"🟢 *SERVER STATUS:* `ONLINE`\n"
            f"⏳ *RUNTIME:* `{uptime}`\n"
            f"⚙️ *ACTIVE ENGINES:* `{len(bg_processes)}`\n"
            f"⚡️ *CONNECTION:* `SECURE`"
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_sysinfo":
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        text = f"🧬 *SYSTEM VITALS:*\n*CPU Usage:* `{cpu}%` 🔥\n*RAM Usage:* `{ram}%` 🧠"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_memory":
        mem = psutil.virtual_memory()
        text = (
            f"🧠 *MEMORY CORE:*\n"
            f"*Total:* `{mem.total / (1024**3):.2f} GB`\n"
            f"*Used:* `{mem.used / (1024**3):.2f} GB` ({mem.percent}%) ⚡️\n"
            f"*Available:* `{mem.available / (1024**3):.2f} GB`"
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_disk":
        disk = psutil.disk_usage('/')
        text = (
            f"💽 *STORAGE VAULT:*\n"
            f"*Total:* `{disk.total / (1024**3):.2f} GB`\n"
            f"*Used:* `{disk.used / (1024**3):.2f} GB` ({disk.percent}%) 📂\n"
            f"*Free:* `{disk.free / (1024**3):.2f} GB`"
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_ps":
        text, markup = render_engines(with_back=True)
        if not text:
            text = "💤 *[SYSTEM IDLE]* No background engines currently active."
            markup = get_back_keyboard()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_myid":
        text = f"🪪 *YOUR TELEGRAM ID:* `{call.from_user.id}` ⚡️"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_help":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=get_help_text(),
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        bot.answer_callback_query(call.id)

    elif call.data == "btn_list_users":
        if not is_owner(user_id): return
        users_list_str = "\n".join([f"▪️ `{uid}`" for uid in allowed_users])
        text = f"👥 *[WHITELISTED USERS]*\n\n{users_list_str}\n\n• Use `/add <id>` or `/remove <id>`."
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )
        bot.answer_callback_query(call.id)

    elif call.data == "cancel_channel_setup":
        waiting_for_channel_forward.discard(user_id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Channel setup was cancelled."
        )
        bot.answer_callback_query(call.id)

print("⚡️ SK HOST is online and waiting...")
threading.Thread(target=restore_services, daemon=True).start()
def _skip_pending_updates():
    """Purane pending updates skip karta hai. 409 conflict aaye to crash nahi, retry karta hai."""
    for _ in range(10):
        try:
            bot.get_updates(offset=-1, timeout=1)
            return
        except ApiTelegramException as e:
            if "409" in str(e) or "Conflict" in str(e):
                print("[!] 409 Conflict: is token ko koi aur jagah bhi chala raha hai. 5s me retry...")
                time.sleep(5)
                continue
            print(f"[!] skip_pending error: {e}")
            return
        except Exception as e:
            print(f"[!] skip_pending error: {e}")
            time.sleep(3)

_skip_pending_updates()

# Polling kabhi band nahi hogi: koi bhi error aaye to 5s baad dobara start
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"[!] Polling crashed: {type(e).__name__}: {e} -> 5s me restart")
        time.sleep(5)
