import logging
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import uvicorn

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "8768201104:AAGB61sD2Gmdjst90s37yg7fm1NHL9yncug"
ADMIN_ID = 8295783400
START_BALANCE = 1000
CURRENCY = "Olmos"

# Diqqat! KANAL_ID qismiga o'zingizning kanalingiz userneymini yozib qo'ying (boshiga @ bilan)
KANAL_ID = "@mening_kanalim"  
# ====================================================

# Render xostingidan havola olganimizdan keyin bu URL avtomatlashtiriladi
SERVER_URL = "https://mukammal-bot.onrender.com" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Ma'lumotlar bazasi (Vaqtinchalik xotira)
users_db = {}

# --- BOT LOGIKASI ---
def get_main_menu(user_id):
    web_app_url = f"{SERVER_URL}/profile/{user_id}"
    
    kb = [
        [InlineKeyboardButton(text="🌐 Shaxsiy Saytni Ochish", web_app=WebAppInfo(url=web_app_url))]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="👨‍💻 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=KANAL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return True

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    uid = message.from_user.id
    name = message.from_user.first_name
    
    if uid not in users_db:
        users_db[uid] = {"name": name, "balance": START_BALANCE, "claimed": False}
        
    if not await check_sub(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{KANAL_ID.replace('@','')}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub_cb")]
        ])
        await message.answer("Bot va Saytdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=kb)
        return

    await message.answer(f"Salom {name}!\nSizga {START_BALANCE} {CURRENCY} taqdim etildi. Profilingizga kiring 👇", 
                         reply_markup=get_main_menu(uid))

@dp.callback_query(F.data == "check_sub_cb")
async def check_sub_cb(call: types.CallbackQuery):
    uid = call.from_user.id
    if await check_sub(uid):
        await call.message.edit_text("Rahmat! Profilingiz tayyor 👇", reply_markup=get_main_menu(uid))
    else:
        await call.answer("Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

# --- ADMIN PANEL LOGIKASI ---
@dp.callback_query(F.data == "admin_panel")
async def admin_main(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stat")],
        [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_send")]
    ])
    await call.message.edit_text("👨‍💻 Admin Panel:", reply_markup=kb)

@dp.callback_query(F.data == "admin_stat")
async def admin_stat(call: types.CallbackQuery):
    await call.answer(f"📊 Jami a'zolar: {len(users_db)} ta", show_alert=True)

@dp.callback_query(F.data == "admin_send")
async def admin_send(call: types.CallbackQuery):
    for user_id in users_db.keys():
        try:
            await bot.send_message(chat_id=user_id, text="🚀 Botimiz va Saytimiz yangilandi! Kirib yangi keyslarni oching.")
        except:
            continue
    await call.answer("✅ Xabar hamma foydalanuvchilarga tarqatildi!", show_alert=True)

# --- SAYT (WEB APP) LOGIKASI ---
@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def user_profile(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {"name": "Mehmon", "balance": START_BALANCE, "claimed": False}
        
    user = users_db[user_id]
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shaxsiy Profil</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #0f172a; color: white; text-align: center; padding: 20px; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); margin-bottom: 20px; }}
            h1 {{ color: #38bdf8; }}
            .balance {{ font-size: 24px; color: #34d399; font-weight: bold; margin: 15px 0; }}
            button {{ background: #38bdf8; color: #0f172a; border: none; padding: 12px 25px; font-size: 16px; border-radius: 8px; cursor: pointer; margin: 5px; width: 85%; font-weight: bold; }}
            button:hover {{ background: #7dd3fc; }}
            .bonus-btn {{ background: #475569; color: white; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>👤 {user['name']}</h1>
            <p>Shaxsiy profilingizga xush kelibsiz</p>
            <div class="balance">💎 Balans: <span id="bal">{user['balance']}</span> {CURRENCY}</div>
        </div>

        <div class="card">
            <h3>🔑 Omad Keysi</h3>
            <p>Narxi: 200 {CURRENCY}</p>
            <button onclick="openCase()">🔑 Keysni Ochish</button>
        </div>

        <div class="card">
            <h3>🎁 Kunlik Bonus</h3>
            <button class="bonus-btn" onclick="getBonus()">🎁 Bonusni Olish</button>
        </div>

        <script>
            async function openCase() {{
                const res = await fetch('/api/opencase/{user_id}');
                const data = await res.json();
                alert(data.msg);
                if(data.success) {{
                    document.getElementById('bal').innerText = data.new_balance;
                }}
            }}

            async function getBonus() {{
                const res = await fetch('/api/bonus/{user_id}');
                const data = await res.json();
                alert(data.msg);
                if(data.success) {{
                    document.getElementById('bal').innerText = data.new_balance;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# --- SAYT FUNKSIYALARI API ---
@app.get("/api/opencase/{user_id}")
async def api_open_case(user_id: int):
    if users_db[user_id]["balance"] >= 200:
        users_db[user_id]["balance"] -= 200
        # 200 olmos yechib, 500 olmos yutuq berish logikasi
        users_db[user_id]["balance"] += 500
        return {"success": True, "msg": "🎉 Keys ochildi! Siz 500 {CURRENCY} yutdingiz!", "new_balance": users_db[user_id]["balance"]}
    else:
        return {"success": False, "msg": "❌ Balansda yetarli {CURRENCY} mavjud emas!"}

@app.get("/api/bonus/{user_id}")
async def api_bonus(user_id: int):
    if users_db[user_id]["claimed"]:
        return {"success": False, "msg": "❌ Siz bugungi bonusni olib bo'lgansiz!"}
    else:
        users_db[user_id]["balance"] += 100
        users_db[user_id]["claimed"] = True
        return {"success": True, "msg": "🎁 Sizga 100 {CURRENCY} bonus berildi!", "new_balance": users_db[user_id]["balance"]}

async def start_bot():
    asyncio.create_task(dp.start_polling(bot))

@app.on_event("startup")
async def on_startup():
    await start_bot()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

