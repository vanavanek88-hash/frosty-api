import asyncio
import os
import secrets
import string
import threading
import time
from datetime import datetime

import discord
from discord.ext import commands
from flask import Flask, jsonify, request

# ============================================================
# НАСТРОЙКИ
# ============================================================
CODE_LENGTH = 6
CODE_TTL = 300
PORT = int(os.environ.get("PORT", 8080))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

ADMIN_DISCORD_ID = 701730050172518420 # Твой ID

lock = threading.Lock()
codes = {}
links = {}
premium_until = {}
premium_keys = {}
discord_avatars = {} # userId -> avatarUrl

CODE_ALPHABET = string.ascii_uppercase + string.digits

def parse_uid(value):
    try: return int(value) if int(value) > 0 else None
    except: return None

def purge_expired_locked(now):
    for c in [c for c, d in codes.items() if now - d["time"] > CODE_TTL]:
        del codes[c]

# ============================================================
# FLASK API
# ============================================================
app = Flask(__name__)

@app.get("/status")
def status():
    uid = parse_uid(request.args.get("userId"))
    if uid is None: return jsonify(error="bad userId"), 400
    now = int(time.time())
    with lock:
        until = premium_until.get(uid, 0)
        link = links.get(uid)
        avatar = discord_avatars.get(uid, "")
            
    is_premium = until > now
    return jsonify(
        linked=link is not None,
        discordName=link["discordName"] if link else "",
        avatarUrl=avatar,
        premium=is_premium,
        premiumUntil=until if is_premium else 0,
    )

@app.post("/link/start")
def link_start():
    data = request.get_json(silent=True) or {}
    uid = parse_uid(data.get("userId"))
    if uid is None: return jsonify(error="bad userId"), 400
    now = time.time()
    with lock:
        purge_expired_locked(now)
        for c in [c for c, d in codes.items() if d["userId"] == uid]: del codes[c]
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        codes[code] = {"userId": uid, "username": str(data.get("username") or "")[:50], "discordId": None, "discordName": None, "time": now}
    return jsonify(code=code, expiresIn=CODE_TTL)

@app.get("/link/status")
def link_status():
    code = (request.args.get("code") or "").strip().upper()
    now = time.time()
    with lock:
        entry = codes.get(code)
        if entry is None: return jsonify(status="expired")
        if now - entry["time"] > CODE_TTL:
            del codes[code]
            return jsonify(status="expired")
        if entry["discordId"] is None: return jsonify(status="pending")
        return jsonify(status="linked", discordId=entry["discordId"], discordName=entry["discordName"])

@app.post("/premium/activate")
def activate_premium():
    data = request.get_json(silent=True) or {}
    uid = parse_uid(data.get("userId"))
    key = str(data.get("key") or "").strip().upper()
    
    if uid is None: return jsonify(error="bad userId"), 400
    if not key: return jsonify(error="bad key"), 400
    
    now = int(time.time())
    with lock:
        key_data = premium_keys.get(key)
        if not key_data: return jsonify(error="Ключ не найден"), 404
        if key_data["used"]: return jsonify(error="Ключ уже использован"), 400
            
        key_data["used"] = True
        days = key_data["days"]
        current_until = premium_until.get(uid, 0)
        base_time = max(now, current_until)
        new_until = base_time + (days * 86400)
        premium_until[uid] = new_until
        
    return jsonify(ok=True, days=days, premiumUntil=new_until)

# ============================================================
# DISCORD-БОТ
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"[bot] вошёл как {bot.user} (id={bot.user.id})")

@bot.command(name="help")
async def help_command(ctx):
    await ctx.send("**❄️ Frosty Hub — Помощь**\n\n`!link <код>` — Привязать Discord.\n`!premium <ID> <дней>` — Выдать Premium.\n`!genkey <дней>` — Сгенерировать ключ.")

@bot.command(name="link")
async def link_command(ctx, code: str = None):
    if not code: return await ctx.send("Использование: `!link КОД`")
    code = code.strip().upper()
    now = time.time()
    with lock:
        entry = codes.get(code)
        if entry is None: return await ctx.send("❌ Код не найден.")
        if now - entry["time"] > CODE_TTL:
            del codes[code]
            return await ctx.send("⌛ Код истёк.")
        if entry["discordId"] is not None: return await ctx.send("⚠️ Код уже использован.")
        
        # Получаем аватарку
        avatar_url = str(ctx.author.display_avatar.url) if ctx.author.display_avatar else ""
        discord_avatars[entry["userId"]] = avatar_url
        
        entry["discordId"] = str(ctx.author.id)
        entry["discordName"] = str(ctx.author.name)
        links[entry["userId"]] = {"discordId": str(ctx.author.id), "discordName": str(ctx.author.name)}
        
    await ctx.send("✅ Аккаунт успешно привязан к Frosty Hub!")

@bot.command(name="premium")
async def premium_command(ctx, roblox_id: int = None, days: int = 30):
    if ctx.author.id != ADMIN_DISCORD_ID: return await ctx.send("❌ Нет прав.")
    if not roblox_id: return await ctx.send("Использование: `!premium <ID> <дней>`")
    now = int(time.time())
    with lock:
        current_until = premium_until.get(roblox_id, 0)
        new_until = max(now, current_until) + (days * 86400)
        premium_until[roblox_id] = new_until
    await ctx.send(f"✅ Выдан Premium на {days} дн. (ID: `{roblox_id}`)")

@bot.command(name="genkey")
async def genkey_command(ctx, days: int = 30):
    if ctx.author.id != ADMIN_DISCORD_ID: return await ctx.send("❌ Нет прав.")
    key = "FROSTY-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    with lock: premium_keys[key] = {"days": days, "used": False}
    await ctx.send(f"🔑 Ключ на **{days}** дней:\n`{key}`\nВведи его в игре.")

def run_bot():
    if not BOT_TOKEN: return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(bot.start(BOT_TOKEN))
    except Exception as e: print(f"[bot] остановлен: {e!r}")

if __name__ == "__main__":
    threading.Thread(target=run_bot, name="discord-bot", daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True, use_reloader=False)
