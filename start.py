import asyncio
import os
from fastapi import FastAPI
import uvicorn
import bot

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

async def main():
    asyncio.create_task(bot.main())

    port = int(os.environ.get("PORT", 10000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
