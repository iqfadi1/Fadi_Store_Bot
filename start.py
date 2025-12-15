import os
import asyncio
import uvicorn
from fastapi import FastAPI
from bot import dp, bot
import db

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

async def start_bot():
    db.init_db()
    db.seed_packages()
    print("BOT READY")
    await dp.start_polling(bot)

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
