import aiosqlite
import json
import uuid
from datetime import datetime
from config import settings

async def init_db():
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                filename TEXT,
                file_size INTEGER,
                created_at TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                is_demo INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def create_analysis(filename: str, file_size: int, is_demo: bool = False) -> str:
    analysis_id = uuid.uuid4().hex
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "INSERT INTO analyses (id, filename, file_size, created_at, status, is_demo) VALUES (?,?,?,?,?,?)",
            (analysis_id, filename, file_size, datetime.utcnow().isoformat(), "processing", int(is_demo))
        )
        await db.commit()
    return analysis_id

async def update_analysis(analysis_id: str, status: str, result: dict):
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "UPDATE analyses SET status=?, result=? WHERE id=?",
            (status, json.dumps(result), analysis_id)
        )
        await db.commit()

async def get_analysis(analysis_id: str) -> dict | None:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            if data.get("result"):
                data["result"] = json.loads(data["result"])
            return data

async def list_analyses(limit: int = 20) -> list:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, filename, file_size, created_at, status, is_demo FROM analyses ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
