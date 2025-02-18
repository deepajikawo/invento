import streamlit as st
from models import Session, User
from datetime import datetime

def init_auth():
    if 'user' not in st.session_state:
        st.session_state.user = None

def register_user(username, email, password, is_admin=False):
    session = Session()
    try:
        # Check if username or email already exists
        if session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first():
            return False, "Username or email already exists"

        # Create new user
        user = User(
            username=username,
            email=email,
            is_admin=is_admin
        )
        user.set_password(password)

        session.add(user)
        session.commit()
        return True, "Registration successful"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def login_user(username, password):
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if user and user.check_password(password):
            user.last_login = datetime.now()
            session.commit()
            st.session_state.user = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
            return True, "Login successful"
        return False, "Invalid username or password"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def logout_user():
    st.session_state.user = None

def require_auth():
    init_auth()
    if not st.session_state.user:
        st.warning("Please log in to access this page")
        show_login_page()
        st.stop()

def require_admin():
    require_auth()
    if not st.session_state.user.get('is_admin'):
        st.error("Admin access required")
        st.stop()

def show_login_page():
    # Custom CSS for styling
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 16px;
        }
        .form-container {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # App logo and title
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center'>
                <h1 style='color: #2E4053'>📱 Austin Phones and Gadgets</h1>
                <p style='color: #566573'>Inventory Management System</p>
            </div>
        """, unsafe_allow_html=True)

    # Show registration tab only for admins
    if st.session_state.user and st.session_state.user.get('is_admin'):
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Manage Users"])
    else:
        tab1 = st.tabs(["🔑 Login"])[0]

    with tab1:
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("### 👤 Welcome Back!")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_button = st.form_submit_button("🚀 Login", 
                    use_container_width=True,
                    help="Click to log in to your account")

            if submit_button:
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success("🎉 " + message)
                        st.rerun()
                    else:
                        st.error("❌ " + message)
                else:
                    st.error("⚠️ Please fill in all fields")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        require_admin()  # Ensure only admins can access this tab
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        
        # User creation form
        with st.form("create_user_form"):
            st.markdown("### 👥 Create New User")
            new_username = st.text_input("Username", placeholder="Choose a username")
            new_email = st.text_input("Email", placeholder="Enter email")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            is_admin = st.checkbox("Grant Admin Access")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                create_button = st.form_submit_button("➕ Create User", 
                    use_container_width=True)

            if create_button:
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        success, message = register_user(new_username, new_email, new_password, is_admin)
                        if success:
                            st.success("🎉 " + message)
                            st.rerun()
                        else:
                            st.error("❌ " + message)
                else:
                    st.error("⚠️ Please fill in all fields")
        
        # Display existing users with edit functionality
        st.markdown("### 📋 Existing Users")
        session = Session()
        users = session.query(User).all()
        for user in users:
            with st.expander(f"👤 {user.username}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📧 Email: {user.email}")
                    st.write("🔑 Admin" if user.is_admin else "👥 Regular User")
                with col2:
                    new_admin_status = st.checkbox("Admin Access", value=user.is_admin, key=f"admin_{user.id}")
                    if st.button("Update Role", key=f"update_{user.id}"):
                        user.is_admin = new_admin_status
                        session.commit()
                        st.success("User role updated successfully!")
                        st.rerun()
                    
                    if st.button("Delete User", key=f"delete_{user.id}"):
                        if user.id != st.session_state.user.get('id'):
                            session.delete(user)
                            session.commit()
                            st.success("User deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Cannot delete your own account!")
        session.close()
        st.markdown("</div>", unsafe_allow_html=True)

    # Password change section for logged-in users
    if st.session_state.user:
        st.markdown("### 🔒 Change Password")
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if new_password != confirm_new_password:
                    st.error("New passwords do not match!")
                else:
                    session = Session()
                    user = session.query(User).filter_by(id=st.session_state.user['id']).first()
                    if user and user.check_password(current_password):
                        user.set_password(new_password)
                        session.commit()
                        st.success("Password changed successfully!")
                    else:
                        st.error("Current password is incorrect!")
                    session.close()

    # Footer
    st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #566573'>
            <p>Secure login powered by Austin Phones and Gadgets IMS</p>
        </div>
    """, unsafe_allow_html=True)