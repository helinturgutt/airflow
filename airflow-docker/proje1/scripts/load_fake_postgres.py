import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="fakestoredb",
    user="fakeuser",
    password="fakepass"
)

cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT,
        price NUMERIC
    );
""")

cur.execute("""
    INSERT INTO products (name, price)
    VALUES 
    ('T-Shirt', 19.99),
    ('Shoes', 49.99),
    ('Backpack', 29.99)
    ON CONFLICT DO NOTHING;
""")

conn.commit()
cur.close()
conn.close()
