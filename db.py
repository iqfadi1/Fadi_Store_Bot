import sqlite3

DB = "bot.db"


def conn():
    return sqlite3.connect(DB)


# ================= INIT =================

def init_db():
    c = conn()
    cur = c.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        balance INTEGER DEFAULT 0
    )
    """)

    # PACKAGES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        active INTEGER DEFAULT 1
    )
    """)

    # ORDERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        package_id INTEGER,
        user_number TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    c.commit()
    c.close()


# ================= USERS =================

def create_user(phone, password_hash):
    c = conn()
    c.execute(
        "INSERT INTO users(phone, balance) VALUES(?,0)",
        (phone,)
    )
    c.commit()
    c.close()


def get_user_by_phone(phone):
    c = conn()
    r = c.execute(
        "SELECT * FROM users WHERE phone=?",
        (phone,)
    ).fetchone()
    c.close()
    return dict(zip(["id", "phone", "balance"], r)) if r else None


def get_user_by_id(uid):
    c = conn()
    r = c.execute(
        "SELECT * FROM users WHERE id=?",
        (uid,)
    ).fetchone()
    c.close()
    return dict(zip(["id", "phone", "balance"], r)) if r else None


def add_balance(phone, amt):
    c = conn()
    c.execute(
        "UPDATE users SET balance = balance + ? WHERE phone=?",
        (amt, phone)
    )
    c.commit()
    c.close()


def set_balance(phone, amt):
    c = conn()
    c.execute(
        "UPDATE users SET balance = ? WHERE phone=?",
        (amt, phone)
    )
    c.commit()
    c.close()


def deduct_balance(phone, amt):
    c = conn()
    c.execute(
        "UPDATE users SET balance = balance - ? WHERE phone=?",
        (amt, phone)
    )
    c.commit()
    c.close()


# ================= PACKAGES =================

def list_packages(active_only=True):
    c = conn()
    if active_only:
        r = c.execute(
            "SELECT id,name,price,active FROM packages WHERE active=1"
        ).fetchall()
    else:
        r = c.execute(
            "SELECT id,name,price,active FROM packages"
        ).fetchall()
    c.close()
    return [
        dict(zip(["id", "name", "price", "active"], row))
        for row in r
    ]


def add_package(name, price):
    c = conn()
    c.execute(
        "INSERT INTO packages(name,price,active) VALUES(?,?,1)",
        (name, price)
    )
    c.commit()
    c.close()


def set_package_price(pid, price):
    c = conn()
    c.execute(
        "UPDATE packages SET price=? WHERE id=?",
        (price, pid)
    )
    c.commit()
    c.close()


def set_package_name(pid, name):
    c = conn()
    c.execute(
        "UPDATE packages SET name=? WHERE id=?",
        (name, pid)
    )
    c.commit()
    c.close()


def disable_package(pid):
    c = conn()
    c.execute(
        "UPDATE packages SET active=0 WHERE id=?",
        (pid,)
    )
    c.commit()
    c.close()


# ================= ORDERS =================

def create_order(uid, package_id, user_number):
    c = conn()
    c.execute(
        "INSERT INTO orders(user_id,package_id,user_number) VALUES(?,?,?)",
        (uid, package_id, user_number)
    )
    c.commit()
    oid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return oid


def get_order(oid):
    c = conn()
    r = c.execute("""
    SELECT 
        o.id,
        u.phone,
        o.user_number,
        p.name,
        p.price,
        u.balance,
        o.status
    FROM orders o
    JOIN users u ON o.user_id = u.id
    JOIN packages p ON o.package_id = p.id
    WHERE o.id=?
    """, (oid,)).fetchone()
    c.close()

    if not r:
        return None

    keys = [
        "id", "phone", "user_number",
        "package_name", "package_price",
        "balance", "status"
    ]
    return dict(zip(keys, r))


def list_user_orders(uid):
    c = conn()
    r = c.execute("""
    SELECT o.id,p.name,p.price,o.status
    FROM orders o
    JOIN packages p ON o.package_id=p.id
    WHERE o.user_id=?
    ORDER BY o.id DESC
    """, (uid,)).fetchall()
    c.close()

    return [
        dict(zip(["id", "package", "price", "status"], row))
        for row in r
    ]


def update_order_status(oid, status):
    c = conn()
    c.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, oid)
    )
    c.commit()
    c.close()


# ================= HELPERS =================

def fmt_lbp(x: int) -> str:
    return f"{x:,}"
