import sqlite3
conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name FROM message_templates WHERE module_type="GROUP_BOT"')
for r in cursor.fetchall():
    print(f'{r[0]}: {r[1]}')
conn.close()
