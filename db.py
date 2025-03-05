import aiosqlite

from config import DB_PATH


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = None

    async def init(self):
        self.db = await aiosqlite.connect(self.db_path)

    async def commit(self):
        await self.db.commit()

    async def execute(self, *args) -> aiosqlite.Cursor:
        return await self.db.execute(*args)
    
    async def fetchone(self, *args):
        cursor = await self.db.execute(*args)
        return await cursor.fetchone()


async def update_database(db: Database):
    await db.execute('''CREATE TABLE IF NOT EXISTS users (
        account_id INTEGER,
        tg_id INTEGER PRIMARY KEY,
        name TEXT,
        role TEXT
    );''')
    await db.commit()

db = Database(DB_PATH)