import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Check message_templates
if 'message_templates' in tables:
    cursor.execute("SELECT COUNT(*) FROM message_templates")
    count = cursor.fetchone()[0]
    print(f"message_templates count: {count}")
    
    cursor.execute("SELECT id, name, channel_type FROM message_templates LIMIT 5")
    for row in cursor.fetchall():
        print(f"  - ID: {row[0]}, Name: {row[1]}, Channel: {row[2]}")

conn.close()
