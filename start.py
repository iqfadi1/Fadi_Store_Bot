import asyncio
import os
from fastapi import FastAPI
import uvicorn
import bot

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

async def run():
    asyncio.create_task(bot.main())
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    asyncio.run(run())
