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
                <h1 style='color: #2E4053'>📱 Phone Shop</h1>
                <p style='color: #566573'>Inventory Management System</p>
            </div>
        """, unsafe_allow_html=True)

    # Login/Register tabs with icons
    tab1, tab2 = st.tabs(["🔑 Login", "✨ Register"])

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
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        with st.form("register_form"):
            st.markdown("### 🌟 Create Account")
            new_username = st.text_input("Username", placeholder="Choose a username")
            new_email = st.text_input("Email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                register_button = st.form_submit_button("✨ Register", 
                    use_container_width=True,
                    help="Click to create your account")

            if register_button:
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        success, message = register_user(new_username, new_email, new_password)
                        if success:
                            st.success("🎉 " + message)
                            success, _ = login_user(new_username, new_password)
                            if success:
                                st.rerun()
                        else:
                            st.error("❌ " + message)
                else:
                    st.error("⚠️ Please fill in all fields")
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style='text-align: center; margin-top: 20px; color: #566573'>
            <p>Secure login powered by Phone Shop IMS</p>
        </div>
    """, unsafe_allow_html=True)