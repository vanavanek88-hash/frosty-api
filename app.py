import asyncio
import os
import secrets
import string
import threading
import time
from datetime import datetime, timedelta

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

# 👇 ТВОЙ DISCORD ID (узнай у @userinfobot). Только ты сможешь выдавать премиум.
ADMIN_DISCORD_ID = 701730050172518420 # <-- ЗАМЕНИ НА СВОЙ ID

# Хранилище (в памяти)
lock = threading.Lock()
codes = {}           # code -> {userId, username, discordId, discordName, time}
links = {}           # userId -> {discordId, discordName}
premium_until = {}   # userId -> unix-время окончания подписки
premium_keys = {}    # key -> {days, used: False}  (ключи активации)

CODE_ALPHABET = string.ascii_uppercase + string.digits


def parse_uid(value):
    try: return int(value) if int(value) > 0 else None
    except: return None

def purge_expired_locked(now):
    for c in [c for c, d in codes.items() if now - d["time"] > CODE_TTL]:
        del codes[c]

# ============================================================
# FLASK API (для игры)
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
    is_premium = until > now
    return jsonify(
        linked=link is not None,
        discordName=link["discordName"] if link else "",
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

@app.post("/unlink")
def unlink():
    data = request.get_json(silent=True) or {}
    uid = parse_uid(data.get("userId"))
    if uid is None: return jsonify(error="bad userId"), 400
    with lock:
        links.pop(uid, None)
        for c in [c for c, d in codes.items() if d["userId"] == uid]: del codes[c]
    return jsonify(ok=True)

# ============================================================
# DISCORD-БОТ
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"[bot] вошёл как {bot.user} (id={bot.user.id})")

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
        entry["discordId"] = str(ctx.author.id)
        entry["discordName"] = str(ctx.author.name)
        links[entry["userId"]] = {"discordId": str(ctx.author.id), "discordName": str(ctx.author.name)}
    await ctx.send("✅ Аккаунт успешно привязан к Frosty Hub!")

# 🔥 НОВОЕ: Админ-команда для выдачи премиума
@bot.command(name="premium")
async def premium_command(ctx, roblox_id: int = None, days: int = 30):
    if ctx.author.id != ADMIN_DISCORD_ID:
        return await ctx.send("❌ У тебя нет прав на использование этой команды.")
    if not roblox_id:
        return await ctx.send("Использование: `!premium <RobloxUserId> <дней>`")
    
    now = int(time.time())
    with lock:
        # Если у игрока уже есть премиум, добавляем дни к текущей дате
        current_until = premium_until.get(roblox_id, 0)
        base_time = max(now, current_until)
        new_until = base_time + (days * 86400)
        premium_until[roblox_id] = new_until
    
    date_str = datetime.fromtimestamp(new_until).strftime('%d.%m.%Y %H:%M')
    await ctx.send(f"✅ Игроку с ID `{roblox_id}` выдан Premium на {days} дн. (до {date_str})")

# 🔥 НОВОЕ: Генерация ключа на 30 дней (только для админа)
@bot.command(name="genkey")
async def genkey_command(ctx, days: int = 30):
    if ctx.author.id != ADMIN_DISCORD_ID:
        return await ctx.send("❌ У тебя нет прав.")
    
    key = "FROSTY-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    with lock:
        premium_keys[key] = {"days": days, "used": False}
    
    await ctx.send(f"🔑 Твой ключ на **{days}** дней:\n`{key}`\nВведи его в игре в меню Premium.")

def run_bot():
    if not BOT_TOKEN: return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try: loop.run_until_complete(bot.start(BOT_TOKEN))
    except Exception as e: print(f"[bot] остановлен: {e!r}")

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    threading.Thread(target=run_bot, name="discord-bot", daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True, use_reloader=False)
