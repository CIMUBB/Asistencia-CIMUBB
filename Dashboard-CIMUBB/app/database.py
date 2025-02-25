import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME", "cimubb_asistencia"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            min_size=1,
            max_size=4,
            ssl=False
        )
        
        async with self.pool.acquire() as conn:
            encoding = await conn.fetchval("SHOW server_encoding;")
            if encoding != "UTF8":
                raise ValueError(f"La BD no está en UTF-8, {encoding}")
    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()