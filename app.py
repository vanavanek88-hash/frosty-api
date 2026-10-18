import os
import json
import random
import string
import time
from flask import Flask, request, jsonify
import discord
from discord.ext import commands
import threading

app = Flask(__name__)

# Хранилище кодов привязки (в памяти)
links = {}

# СЕКРЕТНЫЙ ТОКЕН БОТА (ОБЯЗАТЕЛЬНО ЗАМЕНИ)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================================
# 1. API ДЛЯ ИГРЫ (Твой скрипт Frosty Hub)
# ==========================================
@app.route('/link/start', methods=['POST'])
def start():
    data = request.json
    user_id = data.get('userId')
    # Генерируем 6-значный код
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    links[code] = {"userId": user_id, "discordId": None, "discordName": None, "time": time.time()}
    return jsonify({"code": code, "expiresIn": 300})

@app.route('/link/status', methods=['GET'])
def status():
    code = request.args.get('code')
    if code not in links:
        return jsonify({"status": "expired"})
    
    # Проверка на истечение 5 минут
    if time.time() - links[code]["time"] > 300:
        del links[code]
        return jsonify({"status": "expired"})
        
    if links[code]["discordId"]:
        return jsonify({
            "status": "linked", 
            "discordId": links[code]["discordId"], 
            "discordName": links[code]["discordName"]
        })
    return jsonify({"status": "pending"})

@app.route('/unlink', methods=['POST'])
def unlink():
    # В реальном проекте тут нужно удалять из базы данных
    return jsonify({"ok": True})

@app.route('/status', methods=['GET'])
def user_status():
    # Заглушка для проверки Premium
    return jsonify({"linked": False, "premium": False})


# ==========================================
# 2. КОД DISCORD-БОТА (Он сам свяжет аккаунты)
# ==========================================
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен и готов связывать аккаунты!")

@bot.command(name="link")
async def link(ctx, code: str = None):
    if not code:
        await ctx.send("❌ Напиши код после команды: `!link ABC123`")
        return
    
    code = code.upper()
    if code not in links:
        await ctx.send("❌ Код не найден или истек. Сгенерируй новый в игре.")
        return
    
    # Привязываем Discord ID к коду
    links[code]["discordId"] = str(ctx.author.id)
    links[code]["discordName"] = str(ctx.author.name)
    
    await ctx.send(f"✅ Аккаунт **{ctx.author.name}** успешно привязан к Frosty Hub! Вернись в игру, ключ появится сам.")

def run_bot():
    bot.run(BOT_TOKEN)

# ==========================================
# 3. ЗАПУСК (И сайта, и бота одновременно)
# ==========================================
if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запускаем веб-сервер для игры (порт 8080, Railway требует его)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
