import sqlite3
def check_table_exists(table_name):
    conn = sqlite3.connect('garden.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

if check_table_exists('menu_option'):
    print("ตาราง  มีจริง")
    
else:
    print("ตาราง  ไม่มีในฐานข้อมูล")
