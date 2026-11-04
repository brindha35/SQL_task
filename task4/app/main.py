import os
import hmac
import hashlib

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr

from app.database import Base, engine, get_db
from app.models import Customer
from app.auth import verify_api_key

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secured Customer API")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr



@app.post("/customers", dependencies=[Depends(verify_api_key)])
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db)
):
    new_customer = Customer(
        name=customer.name,
        email=customer.email
    )

    db.add(new_customer)

    try:
        db.commit()
        db.refresh(new_customer)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Customer already exists"
        )

    return {
        "id": new_customer.id,
        "name": new_customer.name,
        "email": new_customer.email
    }



@app.get("/customers", dependencies=[Depends(verify_api_key)])
def get_customers(
    page: int = 1,
    per_page: int = 5,
    db: Session = Depends(get_db)
):
    if page < 1 or per_page < 1:
        raise HTTPException(
            status_code=422,
            detail="Invalid pagination values"
        )

    offset = (page - 1) * per_page

    customers = (
        db.query(Customer)
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return {
        "page": page,
        "per_page": per_page,
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email
            }
            for c in customers
        ]
    }



@app.get("/customers/{customer_id}",
         dependencies=[Depends(verify_api_key)])
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer



@app.put("/customers/{customer_id}",
         dependencies=[Depends(verify_api_key)])
def update_customer(
    customer_id: int,
    data: CustomerCreate,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    customer.name = data.name
    customer.email = data.email

    try:
        db.commit()
        db.refresh(customer)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    return customer



@app.delete("/customers/{customer_id}",
            dependencies=[Depends(verify_api_key)])
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    db.delete(customer)
    db.commit()

    return {"message": "Customer deleted successfully"}



@app.post("/webhooks/order-events")
async def order_webhook(
    request: Request,
    x_signature: str = Header(default="")
):
    payload = await request.body()

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        x_signature
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    return {
        "message": "Webhook received successfully"
    }

from fastapi import Form

@app.post("/token")
def generate_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...)
):

    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=400,
            detail="Invalid grant type"
        )

    if client_id != "my-client":
        raise HTTPException(
            status_code=401,
            detail="Invalid client ID"
        )

    if client_secret != "my-client-secret":
        raise HTTPException(
            status_code=401,
            detail="Invalid client secret"
        )

    return {
        "access_token": "sample-access-token",
        "token_type": "bearer",
        "expires_in": 3600
    }