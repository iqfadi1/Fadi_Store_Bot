import sqlite3

DB = "bot.db"

def conn():
    return sqlite3.connect(DB)

def init_db():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        active INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        package_id INTEGER,
        target TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    c.commit()
    c.close()

def seed_packages():
    c = conn()
    if c.execute("SELECT COUNT(*) FROM packages").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO packages(name,price,active) VALUES(?,?,1)",
            [
                ("5.5 GB Package", 550000),
                ("11 GB Package", 720000),
                ("22 GB Package", 1070000)
            ]
        )
        c.commit()
    c.close()

# USERS
def ensure_user(uid):
    c = conn()
    c.execute("INSERT OR IGNORE INTO users(user_id,balance) VALUES(?,0)", (uid,))
    c.commit()
    c.close()

def get_balance(uid):
    c = conn()
    r = c.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    c.close()
    return r[0] if r else 0

def add_balance(uid, amt):
    c = conn()
    ensure_user(uid)
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amt, uid))
    c.commit()
    c.close()

def deduct_balance(uid, amt):
    c = conn()
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amt, uid))
    c.commit()
    c.close()

# PACKAGES
def list_packages():
    c = conn()
    r = c.execute("SELECT id,name,price FROM packages WHERE active=1").fetchall()
    c.close()
    return r

def add_package(name, price):
    c = conn()
    c.execute("INSERT INTO packages(name,price,active) VALUES(?,?,1)", (name, price))
    c.commit()
    c.close()

def update_package_price(pid, price):
    c = conn()
    c.execute("UPDATE packages SET price=? WHERE id=?", (price, pid))
    c.commit()
    c.close()

def update_package_name(pid, name):
    c = conn()
    c.execute("UPDATE packages SET name=? WHERE id=?", (name, pid))
    c.commit()
    c.close()

def disable_package(pid):
    c = conn()
    c.execute("UPDATE packages SET active=0 WHERE id=?", (pid,))
    c.commit()
    c.close()

# ORDERS
def create_order(uid, pid, target):
    c = conn()
    c.execute("INSERT INTO orders(user_id,package_id,target) VALUES(?,?,?)", (uid, pid, target))
    c.commit()
    oid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return oid

def get_order(oid):
    c = conn()
    r = c.execute("""
    SELECT o.user_id,o.status,p.price,p.name
    FROM orders o JOIN packages p ON o.package_id=p.id
    WHERE o.id=?
    """, (oid,)).fetchone()
    c.close()
    return r

def update_order_status(oid, status):
    c = conn()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    c.commit()
    c.close()
