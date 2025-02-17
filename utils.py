import pandas as pd
from datetime import datetime
import streamlit as st
from models import Session, Phone, Sale
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

def record_sale(phone_model, quantity_sold, unit_price, payment_method, customer_name=None, customer_phone=None, notes=None):
    session = Session()
    try:
        # Check if phone exists and has enough stock
        phone = session.query(Phone).filter(Phone.model == phone_model).first()
        if not phone:
            raise ValueError("Phone model not found in inventory")
        if phone.quantity < quantity_sold:
            raise ValueError("Insufficient stock")

        # Create sale record
        total_amount = quantity_sold * unit_price
        sale = Sale(
            phone_model=phone_model,
            quantity_sold=quantity_sold,
            unit_price=unit_price,
            total_amount=total_amount,
            payment_method=payment_method,
            customer_name=customer_name,
            customer_phone=customer_phone,
            notes=notes
        )
        session.add(sale)

        # Update inventory
        phone.quantity -= quantity_sold
        phone.last_updated = datetime.now()

        session.commit()
        return True, "Sale recorded successfully"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def get_sales_data(start_date=None, end_date=None):
    session = Session()
    try:
        query = session.query(Sale)
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)

        sales = query.all()
        if sales:
            data = [{
                'sale_date': sale.sale_date,
                'phone_model': sale.phone_model,
                'quantity_sold': sale.quantity_sold,
                'unit_price': sale.unit_price,
                'total_amount': sale.total_amount,
                'payment_method': sale.payment_method.value,
                'customer_name': sale.customer_name,
                'customer_phone': sale.customer_phone
            } for sale in sales]
            return pd.DataFrame(data)
        else:
            return pd.DataFrame({
                'sale_date': [],
                'phone_model': [],
                'quantity_sold': [],
                'unit_price': [],
                'total_amount': [],
                'payment_method': [],
                'customer_name': [],
                'customer_phone': []
            })
    finally:
        session.close()

def get_sales_summary():
    session = Session()
    try:
        total_sales = session.query(func.sum(Sale.total_amount)).scalar() or 0
        total_units = session.query(func.sum(Sale.quantity_sold)).scalar() or 0
        sales_by_model = session.query(
            Sale.phone_model,
            func.sum(Sale.quantity_sold).label('units_sold'),
            func.sum(Sale.total_amount).label('total_revenue')
        ).group_by(Sale.phone_model).all()

        return {
            'total_sales': total_sales,
            'total_units': total_units,
            'sales_by_model': sales_by_model
        }
    finally:
        session.close()