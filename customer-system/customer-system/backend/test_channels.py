import sqlite3

conn = sqlite3.connect('customer_system.db')
cursor = conn.cursor()

# Check channel_configs
cursor.execute("SELECT * FROM channel_configs")
rows = cursor.fetchall()
print(f"Found {len(rows)} channels")

for row in rows[:5]:
    print(row)

conn.close()
