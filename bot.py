import os, asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
import db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
STATE = {}

# ---------- USER UI ----------
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 My Balance", callback_data="bal")],
        [InlineKeyboardButton(text="📦 Packages", callback_data="pkgs")]
    ])

@dp.message(Command("start"))
async def start(m: Message):
    db.ensure_user(m.from_user.id)
    await m.answer("Welcome 👋", reply_markup=main_kb())

@dp.callback_query(F.data == "bal")
async def bal(c: CallbackQuery):
    bal = db.get_balance(c.from_user.id)
    await c.message.answer(f"Your balance: {bal:,} LBP")
    await c.answer()

@dp.callback_query(F.data == "pkgs")
async def pkgs(c: CallbackQuery):
    rows = db.list_packages()
    kb = []
    for pid, name, price in rows:
        kb.append([
            InlineKeyboardButton(
                text=f"{name} — {price:,} LBP",
                callback_data=f"buy:{pid}"
            )
        ])
    await c.message.answer(
        "Select a package:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await c.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(c: CallbackQuery):
    pid = int(c.data.split(":")[1])
    STATE[c.from_user.id] = pid
    await c.message.answer("Enter phone number / account ID:")
    await c.answer()

@dp.message(~F.text.startswith("/"))
async def text_handler(m: Message):
    if m.from_user.id not in STATE:
        return

    pid = STATE.pop(m.from_user.id)
    oid = db.create_order(m.from_user.id, pid, m.text)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{oid}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{oid}")
        ]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"📦 New Order #{oid}\n"
        f"User ID: {m.from_user.id}\n"
        f"Package ID: {pid}\n"
        f"Target: {m.text}\n\n"
        f"Status: PENDING",
        reply_markup=kb
    )

    await m.answer("Your request has been sent for approval ⏳")

# ---------- ADMIN ----------
@dp.message(Command("packages"))
async def admin_packages(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    rows = db.list_packages()
    text = "📦 Packages List:\n\n"
    for pid, name, price in rows:
        text += f"ID: {pid} | {name} | {price:,} LBP\n"
    await m.answer(text)

@dp.message(Command("addpackage"))
async def add_pkg(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split(maxsplit=2)
    db.add_package(parts[2], int(parts[1].replace(",", "")))
    await m.answer("Package added ✅")

@dp.message(Command("setprice"))
async def set_price(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    _, pid, price = m.text.split()
    db.update_package_price(int(pid), int(price.replace(",", "")))
    await m.answer("Price updated ✅")

@dp.message(Command("setname"))
async def set_name(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split(maxsplit=2)
    db.update_package_name(int(parts[1]), parts[2])
    await m.answer("Name updated ✅")

@dp.message(Command("deletepackage"))
async def delete_pkg(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    pid = int(m.text.split()[1])
    db.disable_package(pid)
    await m.answer("Package removed ✅")

@dp.message(Command("addbalance"))
async def add_bal(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    _, uid, amt = m.text.split()
    amt = int(amt.replace(",", ""))
    db.add_balance(int(uid), amt)
    bal = db.get_balance(int(uid))
    await bot.send_message(
        int(uid),
        f"Your balance has been updated ✅\n"
        f"Added: {amt:,} LBP\n"
        f"Current balance: {bal:,} LBP"
    )
    await m.answer("Balance added ✅")

# ---------- APPROVE / REJECT ----------
@dp.callback_query(F.data.startswith("approve:"))
async def approve(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        return
    oid = int(c.data.split(":")[1])
    order = db.get_order(oid)

    if not order:
        await c.answer("Order not found", show_alert=True)
        return

    uid, pid, status, price, name = order
    if status != "pending":
        await c.answer("Already processed", show_alert=True)
        return

    if db.get_balance(uid) < price:
        db.update_order_status(oid, "rejected")
        await c.message.edit_text("❌ Insufficient balance")
        await bot.send_message(uid, "❌ Order rejected (insufficient balance)")
        return

    db.deduct_balance(uid, price)
    db.update_order_status(oid, "approved")

    await c.message.edit_text(
        f"✅ Order #{oid} APPROVED\n"
        f"Package: {name}\n"
        f"Price: {price:,} LBP"
    )

    await bot.send_message(
        uid,
        f"✅ Your order has been approved!\n"
        f"Package: {name}\n"
        f"Price: {price:,} LBP"
    )

@dp.callback_query(F.data.startswith("reject:"))
async def reject(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        return
    oid = int(c.data.split(":")[1])
    order = db.get_order(oid)

    if not order:
        return

    uid, _, status, _, name = order
    if status != "pending":
        return

    db.update_order_status(oid, "rejected")
    await c.message.edit_text(f"❌ Order #{oid} REJECTED\nPackage: {name}")
    await bot.send_message(uid, "❌ Your order has been rejected.")

async def main():
    db.init_db()
    db.seed_packages()
    print("BOT READY")
    await dp.start_polling(bot)

asyncio.run(main())
