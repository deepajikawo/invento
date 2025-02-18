import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils import (
    load_inventory, 
    save_inventory, 
    validate_input, 
    calculate_total_value,
    get_low_stock_items,
    record_sale,
    get_sales_data,
    get_sales_summary
)
from models import PaymentMethod
from auth import init_auth, require_auth, require_admin, show_login_page, logout_user

# Set page config first, before any other Streamlit commands
st.set_page_config(
    page_title="Austin Phones and Gadgets - Inventory Management",
    page_icon="📱",
    layout="wide"
)

# Initialize session state
if 'inventory_updated' not in st.session_state:
    st.session_state.inventory_updated = False

def main():
    init_auth()

    if st.session_state.user:
        st.title("📱 Austin Phones and Gadgets")

        # User info and logout in sidebar
        with st.sidebar:
            st.write(f"Welcome, {st.session_state.user['username']}!")
            if st.button("Logout"):
                logout_user()
                st.rerun()

        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Dashboard", "Manage Inventory", "Record Sale", "Reports"]
        )

        # Load inventory data
        df = load_inventory()

        if page == "Dashboard":
            show_dashboard(df)
        elif page == "Manage Inventory":
            require_admin()  # Only admins can manage inventory
            show_inventory_management(df)
        elif page == "Record Sale":
            show_sales_management(df)
        else:
            show_reports(df)
    else:
        show_login_page()

def show_dashboard(df):
    st.header("Dashboard")

    # Get sales summary
    sales_summary = get_sales_summary()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Products", len(df))
    with col2:
        st.metric("Total Items in Stock", int(df['quantity'].sum()))
    with col3:
        st.metric("Total Inventory Value", f"₦{calculate_total_value(df):,.2f}")
    with col4:
        st.metric("Total Sales", f"₦{sales_summary['total_sales']:,.2f}")

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
            price = st.number_input("Price (₦)", min_value=0.0, step=0.01)
            quantity = st.number_input("Quantity", min_value=0, value=0, step=1)

            if st.form_submit_button("Add to Inventory"):
                valid, message = validate_input(model, brand, price, quantity)
                if valid:
                    new_item = {
                        'model': model,
                        'brand': brand,
                        'price': price,
                        'quantity': quantity,
                        'last_updated': datetime.now()
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
            current_qty = int(df.loc[item_idx, 'quantity'])

            new_qty = st.number_input(
                "New Quantity",
                min_value=0,
                value=current_qty,
                step=1
            )

            if st.button("Update Stock"):
                df.loc[item_idx, 'quantity'] = new_qty
                df.loc[item_idx, 'last_updated'] = datetime.now()
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

def show_sales_management(df):
    st.header("Record Sale")

    if df.empty:
        st.warning("No items in inventory. Please add items first.")
        return

    with st.form("record_sale_form"):
        # Product selection
        phone_model = st.selectbox("Select Product", df['model'].tolist())
        selected_phone = df[df['model'] == phone_model].iloc[0]

        st.info(f"Available stock: {int(selected_phone['quantity'])} units")
        st.info(f"Unit price: ₦{selected_phone['price']:.2f}")

        # Sale details
        quantity = st.number_input("Quantity", min_value=1, max_value=int(selected_phone['quantity']), value=1)
        unit_price = st.number_input("Unit Price ($)", min_value=0.0, value=float(selected_phone['price']), step=0.01)
        payment_method = st.selectbox("Payment Method", [method.value for method in PaymentMethod])

        # Customer details
        customer_name = st.text_input("Customer Name (Optional)")
        customer_phone = st.text_input("Customer Phone (Optional)")
        notes = st.text_area("Notes (Optional)")

        # Calculate total
        total_amount = quantity * unit_price
        st.write(f"Total Amount: ${total_amount:.2f}")

        if st.form_submit_button("Record Sale"):
            success, message = record_sale(
                phone_model=phone_model,
                quantity_sold=quantity,
                unit_price=unit_price,
                payment_method=PaymentMethod(payment_method),
                customer_name=customer_name,
                customer_phone=customer_phone,
                notes=notes
            )

            if success:
                st.success(message)
                st.session_state.inventory_updated = True
            else:
                st.error(message)

def show_reports(df):
    st.header("Reports")

    # Tabs for different reports
    tab1, tab2, tab3 = st.tabs(["Inventory", "Sales History", "Sales Analytics"])

    with tab1:
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

    with tab2:
        st.subheader("Sales History")
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())

        sales_df = get_sales_data(
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time())
        )

        if not sales_df.empty:
            st.dataframe(sales_df, use_container_width=True)
            if st.button("Export Sales to CSV"):
                sales_df.to_csv('sales_export.csv', index=False)
                st.success("Sales data exported successfully!")
        else:
            st.info("No sales data available for the selected period.")

    with tab3:
        st.subheader("Sales Analytics")
        sales_summary = get_sales_summary()

        # Key metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Sales Revenue", f"₦{sales_summary['total_sales']:,.2f}")
        with col2:
            st.metric("Total Units Sold", sales_summary['total_units'])

        # Sales by model
        if sales_summary['sales_by_model']:
            sales_by_model_df = pd.DataFrame(
                sales_summary['sales_by_model'],
                columns=['Model', 'Units Sold', 'Revenue']
            )
            st.subheader("Sales by Model")
            st.dataframe(sales_by_model_df, use_container_width=True)

            # Revenue by model chart
            fig = px.bar(sales_by_model_df, x='Model', y='Revenue',
                        title="Revenue by Model")
            st.plotly_chart(fig, use_container_width=True)

            # Units sold by model chart
            fig = px.pie(sales_by_model_df, values='Units Sold', names='Model',
                        title="Units Sold Distribution by Model")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data available for analysis.")

if __name__ == "__main__":
    main()