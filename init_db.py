import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("schulden.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS schulden (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schuldner TEXT NOT NULL,
        glaeubiger TEXT NOT NULL,
        betrag REAL NOT NULL,
        datum TEXT NOT NULL,
        dringlichkeit INTEGER DEFAULT 1,
        bezahlt INTEGER DEFAULT 0
    )
""")


conn.commit()
conn.close()

conn = sqlite3.connect("user.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL UNIQUE,
               password TEXT NOT NULL,
               is_admin INTEGER DEFAULT 0
               )
""")


conn.commit()
conn.close()