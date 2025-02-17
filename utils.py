import pandas as pd
from datetime import datetime
import streamlit as st

def load_inventory():
    try:
        df = pd.read_csv('data/inventory.csv')
        return df
    except FileNotFoundError:
        df = pd.DataFrame({
            'model': [],
            'brand': [],
            'price': [],
            'quantity': [],
            'last_updated': []
        })
        df.to_csv('data/inventory.csv', index=False)
        return df

def save_inventory(df):
    df.to_csv('data/inventory.csv', index=False)

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
