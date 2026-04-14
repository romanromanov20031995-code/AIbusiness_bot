import aiosqlite
from datetime import datetime, timedelta
from typing import Optional
from bot.config import DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                product_info TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)
        """)
        
        await db.commit()


async def add_product(name: str, description: str, price: float, image_url: Optional[str] = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)",
            (name, description, price, image_url)
        )
        await db.commit()
        return cursor.lastrowid


async def get_products() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_product(product_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_product(product_id: int, **kwargs) -> bool:
    allowed_fields = {'name', 'description', 'price', 'image_url'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [product_id]
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            f"UPDATE products SET {set_clause} WHERE id = ?",
            values
        )
        await db.commit()
        return True


async def delete_product(product_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()
        return cursor.rowcount > 0


async def add_order(
    user_id: int,
    user_name: str,
    phone: str,
    address: str,
    product_info: str,
    total_amount: float
) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO orders (user_id, user_name, phone, address, product_info, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, user_name, phone, address, product_info, total_amount)
        )
        await db.commit()
        return cursor.lastrowid


async def get_orders(user_id: Optional[int] = None, status: Optional[str] = None) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_order(order_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def complete_order(order_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "UPDATE orders SET status = 'completed', completed_at = ? WHERE id = ?",
            (datetime.now(), order_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_order(order_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        await db.commit()
        return cursor.rowcount > 0


async def clear_old_orders(days: int) -> int:
    cutoff_date = datetime.now() - timedelta(days=days)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM orders WHERE created_at < ? AND status = 'completed'",
            (cutoff_date,)
        )
        await db.commit()
        return cursor.rowcount


async def get_orders_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'") as cursor:
            pending = (await cursor.fetchone())['count']
        
        async with db.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'completed'") as cursor:
            completed = (await cursor.fetchone())['count']
        
        async with db.execute("SELECT COUNT(*) as count FROM products") as cursor:
            products = (await cursor.fetchone())['count']
        
        return {
            'pending_orders': pending,
            'completed_orders': completed,
            'total_products': products
        }
