import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgetSQL",
    user="postgres",
    password="NewPassword123",
    port="5432"
)

def get_orders(customer_id):

    try:
        customer_id = int(customer_id)
    except (ValueError, TypeError):
        return []

    cursor = conn.cursor()

    query = """
        SELECT *
        FROM orders
        WHERE customer_id = %s
    """

    cursor.execute(query, (customer_id,))
    result = cursor.fetchall()

    cursor.close()
    return result


print("Normal Input:", get_orders(1))

print("Injection Input:", get_orders("1 OR 1=1"))

conn.close()