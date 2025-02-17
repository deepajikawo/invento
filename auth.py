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
    st.title("Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Register"):
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = register_user(new_username, new_email, new_password)
                        if success:
                            st.success(message)
                            success, _ = login_user(new_username, new_password)
                            if success:
                                st.experimental_rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")
