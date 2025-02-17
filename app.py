import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils import (
    load_inventory, 
    save_inventory, 
    validate_input, 
    calculate_total_value,
    get_low_stock_items
)

st.set_page_config(
    page_title="Phone Shop Inventory Management",
    layout="wide"
)

# Initialize session state
if 'inventory_updated' not in st.session_state:
    st.session_state.inventory_updated = False

def main():
    st.title("📱 Phone Shop Inventory Management")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Manage Inventory", "Reports"]
    )
    
    # Load inventory data
    df = load_inventory()
    
    if page == "Dashboard":
        show_dashboard(df)
    elif page == "Manage Inventory":
        show_inventory_management(df)
    else:
        show_reports(df)

def show_dashboard(df):
    st.header("Dashboard")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", len(df))
    with col2:
        st.metric("Total Items in Stock", df['quantity'].sum())
    with col3:
        st.metric("Total Inventory Value", f"${calculate_total_value(df):,.2f}")
    
    # Low stock alerts
    st.subheader("⚠️ Low Stock Alerts")
    low_stock = get_low_stock_items(df)
    if not low_stock.empty:
        st.warning("The following items are running low on stock:")
        st.dataframe(low_stock[['model', 'brand', 'quantity']])
    else:
        st.success("All items have sufficient stock!")
    
    # Stock distribution chart
    st.subheader("Stock Distribution")
    if not df.empty:
        fig = px.bar(df, x='model', y='quantity', color='brand',
                     title="Current Stock Levels")
        st.plotly_chart(fig, use_container_width=True)

def show_inventory_management(df):
    st.header("Manage Inventory")
    
    tab1, tab2, tab3 = st.tabs(["Add New Item", "Update Stock", "Remove Item"])
    
    with tab1:
        st.subheader("Add New Phone")
        with st.form("add_phone_form"):
            model = st.text_input("Model Name")
            brand = st.text_input("Brand")
            price = st.number_input("Price ($)", min_value=0.0, step=0.01)
            quantity = st.number_input("Quantity", min_value=0, step=1)
            
            if st.form_submit_button("Add to Inventory"):
                valid, message = validate_input(model, brand, price, quantity)
                if valid:
                    new_item = {
                        'model': model,
                        'brand': brand,
                        'price': price,
                        'quantity': quantity,
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
                    save_inventory(df)
                    st.success("Item added successfully!")
                    st.session_state.inventory_updated = True
                else:
                    st.error(message)
    
    with tab2:
        st.subheader("Update Existing Stock")
        if not df.empty:
            item_to_update = st.selectbox(
                "Select Item to Update",
                df['model'].tolist(),
                key='update_select'
            )
            item_idx = df[df['model'] == item_to_update].index[0]
            current_qty = df.loc[item_idx, 'quantity']
            
            new_qty = st.number_input(
                "New Quantity",
                min_value=0,
                value=current_qty
            )
            
            if st.button("Update Stock"):
                df.loc[item_idx, 'quantity'] = new_qty
                df.loc[item_idx, 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_inventory(df)
                st.success("Stock updated successfully!")
                st.session_state.inventory_updated = True
        else:
            st.info("No items in inventory to update.")
    
    with tab3:
        st.subheader("Remove Item")
        if not df.empty:
            item_to_remove = st.selectbox(
                "Select Item to Remove",
                df['model'].tolist(),
                key='remove_select'
            )
            
            if st.button("Remove Item"):
                df = df[df['model'] != item_to_remove]
                save_inventory(df)
                st.success("Item removed successfully!")
                st.session_state.inventory_updated = True
        else:
            st.info("No items in inventory to remove.")

def show_reports(df):
    st.header("Inventory Reports")
    
    # Current inventory table
    st.subheader("Current Inventory")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Value by brand chart
        st.subheader("Inventory Value by Brand")
        brand_value = df.groupby('brand').apply(
            lambda x: (x['price'] * x['quantity']).sum()
        ).reset_index()
        brand_value.columns = ['Brand', 'Total Value']
        fig = px.pie(brand_value, values='Total Value', names='Brand',
                     title="Inventory Value Distribution by Brand")
        st.plotly_chart(fig, use_container_width=True)
        
        # Export option
        if st.button("Export Inventory to CSV"):
            df.to_csv('inventory_export.csv', index=False)
            st.success("Inventory exported successfully!")
    else:
        st.info("No items in inventory to display.")

if __name__ == "__main__":
    main()
