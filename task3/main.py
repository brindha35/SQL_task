
from database import SessionLocal, engine, Base
from models import Customer, Product, Order
from pymongo import MongoClient



Base.metadata.create_all(bind=engine)




def place_order(customer_id, product_id, qty, force_error=False):

    session = SessionLocal()

    try:
        
        customer = session.query(Customer).filter(
            Customer.id == customer_id
        ).first()

        if customer is None:
            raise Exception("Customer not found")


    
        product = session.query(Product).filter(
            Product.id == product_id
        ).with_for_update().first()

        if product is None:
            raise Exception("Product not found")

        
        if qty <= 0:
            raise Exception("Invalid quantity")

        
        if product.stock < qty:
            raise Exception("Insufficient stock")

        old_stock = product.stock

        
        product.stock -= qty

        session.flush()

    
        if force_error:
            raise Exception("Forced failure")

        
        total = product.price * qty

        
        order = Order(
            customer_id=customer_id,
            product_id=product_id,
            qty=qty,
            total=total
        )

        session.add(order)

        session.commit()

        print(
            f"Order placed: stock {old_stock} -> {product.stock}"
        )

    except Exception as e:

        session.rollback()

        if str(e) == "Forced failure":

            stock = session.query(Product.stock).filter(
                Product.id == product_id
            ).scalar()

            print(
                f"Forced failure: rolled back, stock still {stock}"
            )

        else:
            print("Order failed:", e)

    finally:
        session.close()



def mongo_orders():

    client = MongoClient("mongodb://localhost:27017/")

    db = client["task3_db"]

    orders = db["order_events"]

   
    orders.delete_many({"customer_id": 1})

   
    events = [
        {"customer_id": 1, "total": 200},
        {"customer_id": 1, "total": 250},
        {"customer_id": 1, "total": 300},
        {"customer_id": 1, "total": 250},
        {"customer_id": 1, "total": 300}
    ]

    orders.insert_many(events)

    print("5 order events inserted successfully")


    pipeline = [
        {
            "$group": {
                "_id": "$customer_id",
                "total_amount": {
                    "$sum": "$total"
                }
            }
        }
    ]

    result = orders.aggregate(pipeline)

    for data in result:

        print(
            f"Mongo totals: customer {data['_id']} "
            f"-> {data['total_amount']}"
        )

    client.close()



if __name__ == "__main__":


    with SessionLocal.begin() as session:

        customer = session.query(Customer).filter(
            Customer.id == 1
        ).first()

        if customer is None:
            session.add(
                Customer(
                    id=1,
                    name="Arun",
                    email="arun@gmail.com",
                    phone="9876543210"
                )
            )

        product = session.query(Product).filter(
            Product.id == 1
        ).first()

        if product is None:
            session.add(
                Product(
                    id=1,
                    name="Laptop",
                    price=650,
                    stock=10
                )
            )


    with SessionLocal.begin() as session:

        product = session.get(Product, 1)
        product.stock = 10

    place_order(1, 1, 2)


    with SessionLocal.begin() as session:

        product = session.get(Product, 1)
        product.stock = 10


    place_order(1, 1, 2, force_error=True)


    mongo_orders()
