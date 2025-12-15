import os, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from dotenv import load_dotenv
import db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

STATE = {}
ADMIN_STATE = {}

# ---------- USER UI ----------
def user_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Buy Package", callback_data="pkgs")],
        [InlineKeyboardButton(text="💳 My Balance", callback_data="bal")]
    ])

@dp.message(Command("start"))
async def start(m: Message):
    db.ensure_user(m.from_user.id)
    await m.answer(
        "👋 Welcome to Fadi Store\n\n"
        "✔ Fast activation\n"
        "✔ Secure balance system\n\n"
        "Choose an option below 👇",
        reply_markup=user_kb()
    )

@dp.callback_query(F.data == "bal")
async def bal(c: CallbackQuery):
    bal = db.get_balance(c.from_user.id)
    await c.message.answer(f"💳 Your balance: {bal:,} LBP")
    await c.answer()

@dp.callback_query(F.data == "pkgs")
async def pkgs(c: CallbackQuery):
    rows = db.list_packages()
    kb = []
    for pid, name, price in rows:
        kb.append([InlineKeyboardButton(
            text=f"{name} — {price:,} LBP",
            callback_data=f"buy:{pid}"
        )])
    await c.message.answer(
        "📦 Select a package:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await c.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(c: CallbackQuery):
    pid = int(c.data.split(":")[1])
    STATE[c.from_user.id] = pid
    await c.message.answer("📞 Enter phone number / account ID:")
    await c.answer()

# ---------- MAIN MESSAGE HANDLER (IMPORTANT FIX HERE) ----------
@dp.message(~F.text.startswith("/"))
async def handler(m: Message):
    uid = m.from_user.id

    # USER ORDER FLOW
    if uid in STATE:
        pid = STATE.pop(uid)
        oid = db.create_order(uid, pid, m.text)

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{oid}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{oid}")
        ]])

        await bot.send_message(
            ADMIN_ID,
            f"📦 New Order #{oid}\n"
            f"User ID: {uid}\n"
            f"Target: {m.text}",
            reply_markup=kb
        )
        await m.answer("⏳ Request sent. Waiting for approval.")
        return

    # ADMIN TEXT INPUT
    if uid != ADMIN_ID:
        return

    act = ADMIN_STATE.get("a")

    if act == "add_pkg_name":
        ADMIN_STATE["name"] = m.text
        ADMIN_STATE["a"] = "add_pkg_price"
        await m.answer("Enter price:")
        return

    if act == "add_pkg_price":
        db.add_package(ADMIN_STATE["name"], int(m.text.replace(",", "")))
        ADMIN_STATE.clear()
        await m.answer("✅ Package added", reply_markup=admin_kb())
        return

    if act == "edit_price_id":
        ADMIN_STATE["pid"] = int(m.text)
        ADMIN_STATE["a"] = "edit_price_new"
        await m.answer("New price:")
        return

    if act == "edit_price_new":
        db.update_package_price(
            ADMIN_STATE["pid"],
            int(m.text.replace(",", ""))
        )
        ADMIN_STATE.clear()
        await m.answer("✅ Price updated", reply_markup=admin_kb())
        return

    if act == "edit_name_id":
        ADMIN_STATE["pid"] = int(m.text)
        ADMIN_STATE["a"] = "edit_name_new"
        await m.answer("New name:")
        return

    if act == "edit_name_new":
        db.update_package_name(ADMIN_STATE["pid"], m.text)
        ADMIN_STATE.clear()
        await m.answer("✅ Name updated", reply_markup=admin_kb())
        return

    if act == "delete_pkg":
        db.disable_package(int(m.text))
        ADMIN_STATE.clear()
        await m.answer("🗑 Package deleted", reply_markup=admin_kb())
        return

    if act == "add_bal_uid":
        ADMIN_STATE["uid"] = int(m.text)
        ADMIN_STATE["a"] = "add_bal_amt"
        await m.answer("Amount:")
        return

    if act == "add_bal_amt":
        amt = int(m.text.replace(",", ""))
        db.add_balance(ADMIN_STATE["uid"], amt)
        bal = db.get_balance(ADMIN_STATE["uid"])
        await bot.send_message(
            ADMIN_STATE["uid"],
            f"💰 Balance added: {amt:,} LBP\nCurrent: {bal:,} LBP"
        )
        ADMIN_STATE.clear()
        await m.answer("✅ Balance added", reply_markup=admin_kb())

# ---------- ADMIN PANEL ----------
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 View Packages", callback_data="a_view")],
        [InlineKeyboardButton(text="➕ Add Package", callback_data="a_add")],
        [InlineKeyboardButton(text="✏️ Edit Price", callback_data="a_edit_price")],
        [InlineKeyboardButton(text="✏️ Edit Name", callback_data="a_edit_name")],
        [InlineKeyboardButton(text="🗑 Delete Package", callback_data="a_del")],
        [InlineKeyboardButton(text="💰 Add Balance", callback_data="a_bal")]
    ])

@dp.message(Command("admin"))
async def admin(m: Message):
    if m.from_user.id == ADMIN_ID:
        ADMIN_STATE.clear()
        await m.answer("🔧 Admin Panel", reply_markup=admin_kb())

@dp.callback_query(F.data == "a_view")
async def a_view(c: CallbackQuery):
    rows = db.list_packages()
    text = "📦 Packages:\n\n"
    for pid, n, p in rows:
        text += f"ID {pid} | {n} | {p:,} LBP\n"
    await c.message.answer(text)
    await c.answer()

@dp.callback_query(F.data == "a_add")
async def a_add(c: CallbackQuery):
    ADMIN_STATE["a"] = "add_pkg_name"
    await c.message.answer("Package name:")
    await c.answer()

@dp.callback_query(F.data == "a_edit_price")
async def a_ep(c: CallbackQuery):
    ADMIN_STATE["a"] = "edit_price_id"
    await c.message.answer("Package ID:")
    await c.answer()

@dp.callback_query(F.data == "a_edit_name")
async def a_en(c: CallbackQuery):
    ADMIN_STATE["a"] = "edit_name_id"
    await c.message.answer("Package ID:")
    await c.answer()

@dp.callback_query(F.data == "a_del")
async def a_del(c: CallbackQuery):
    ADMIN_STATE["a"] = "delete_pkg"
    await c.message.answer("Package ID:")
    await c.answer()

@dp.callback_query(F.data == "a_bal")
async def a_bal(c: CallbackQuery):
    ADMIN_STATE["a"] = "add_bal_uid"
    await c.message.answer("User ID:")
    await c.answer()

# ---------- APPROVE / REJECT ----------
@dp.callback_query(F.data.startswith("approve:"))
async def approve(c: CallbackQuery):
    oid = int(c.data.split(":")[1])
    uid, status, price, name = db.get_order(oid)
    if status != "pending":
        return
    if db.get_balance(uid) < price:
        await c.message.edit_text("❌ Insufficient balance")
        return
    db.deduct_balance(uid, price)
    db.update_order_status(oid, "approved")
    await c.message.edit_text(f"✅ Approved\n{name}")
    await bot.send_message(uid, f"✅ Order approved\n{name}")

@dp.callback_query(F.data.startswith("reject:"))
async def reject(c: CallbackQuery):
    oid = int(c.data.split(":")[1])
    uid, status, _, name = db.get_order(oid)
    if status != "pending":
        return
    db.update_order_status(oid, "rejected")
    await c.message.edit_text(f"❌ Rejected\n{name}")
    await bot.send_message(uid, "❌ Order rejected")

# ---------- START ----------
async def main():
    db.init_db()
    db.seed_packages()
    print("BOT READY")
    await dp.start_polling(bot)
