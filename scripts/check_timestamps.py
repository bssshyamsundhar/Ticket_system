"""Check all TIMESTAMP columns in the database"""
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, database='ticketdb', user='postgres', password='shyam123')
cur = conn.cursor()

cur.execute("""
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE data_type = 'timestamp without time zone' 
    AND table_schema = 'public' 
    ORDER BY table_name, ordinal_position
""")
rows = cur.fetchall()
print("=== TIMESTAMP WITHOUT TIME ZONE columns ===")
for r in rows:
    print(f"  {r[0]}.{r[1]}")

cur.execute("""
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE data_type = 'timestamp with time zone' 
    AND table_schema = 'public' 
    ORDER BY table_name, ordinal_position
""")
rows2 = cur.fetchall()
print("\n=== TIMESTAMP WITH TIME ZONE columns ===")
for r in rows2:
    print(f"  {r[0]}.{r[1]}")

conn.close()
