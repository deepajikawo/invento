import pandas as pd
from datetime import datetime
import streamlit as st
from models import Session, Phone
from sqlalchemy import func

def load_inventory():
    session = Session()
    try:
        # Query all phones and convert to DataFrame
        phones = session.query(Phone).all()
        if phones:
            data = [{
                'model': phone.model,
                'brand': phone.brand,
                'price': phone.price,
                'quantity': phone.quantity,
                'last_updated': phone.last_updated
            } for phone in phones]
            return pd.DataFrame(data)
        else:
            return pd.DataFrame({
                'model': [],
                'brand': [],
                'price': [],
                'quantity': [],
                'last_updated': []
            })
    finally:
        session.close()

def save_inventory(df):
    session = Session()
    try:
        # Clear existing records
        session.query(Phone).delete()

        # Add new records
        for _, row in df.iterrows():
            phone = Phone(
                model=row['model'],
                brand=row['brand'],
                price=row['price'],
                quantity=row['quantity'],
                last_updated=datetime.now()
            )
            session.add(phone)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def validate_input(model, brand, price, quantity):
    if not model or not brand:
        return False, "Model and Brand cannot be empty"
    try:
        price = float(price)
        if price <= 0:
            return False, "Price must be greater than 0"
    except ValueError:
        return False, "Price must be a valid number"

    try:
        quantity = int(quantity)
        if quantity < 0:
            return False, "Quantity cannot be negative"
    except ValueError:
        return False, "Quantity must be a valid integer"

    return True, ""

def calculate_total_value(df):
    return (df['price'] * df['quantity']).sum()

def get_low_stock_items(df, threshold=5):
    return df[df['quantity'] <= threshold]