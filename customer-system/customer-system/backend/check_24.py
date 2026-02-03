import sqlite3
conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, module_type FROM message_templates WHERE id=24')
row = cursor.fetchone()
if row:
    print(f'ID: {row[0]}')
    print(f'名称: {row[1]}')
    print(f'module_type: {row[2]}')
conn.close()
