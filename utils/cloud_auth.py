import streamlit as st
import hashlib
import secrets
import datetime

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Generate a secure random token"""
    return secrets.token_hex(16)

def check_credentials(username, password):
    """Check if username and password match predefined credentials"""
    # Initialize the authentication state
    if "auth_tokens" not in st.session_state:
        st.session_state.auth_tokens = {}
    
    # Hash the provided password
    password_hash = hash_password(password)
    
    # Check if the credentials exist in secrets.toml
    try:
        stored_password_hash = st.secrets["credentials"][username]
        if stored_password_hash == password_hash:
            # Generate a token for this session
            token = generate_token()
            # Store the token with username and expiry time
            st.session_state.auth_tokens[token] = {
                "username": username,
                "expires": datetime.datetime.now() + datetime.timedelta(days=1)
            }
            return {"success": True, "token": token, "username": username}
    except (KeyError, TypeError):
        # Either the username doesn't exist or secrets.toml isn't available
        pass
    
    # Fallback to check hardcoded admin credentials (for development)
    if username == "admin" and password_hash == "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9":
        token = generate_token()
        st.session_state.auth_tokens[token] = {
            "username": username,
            "expires": datetime.datetime.now() + datetime.timedelta(days=1)
        }
        return {"success": True, "token": token, "username": username}
    
    return {"success": False, "message": "Invalid username or password"}

def validate_token(token):
    """Validate a token and return the associated username if valid"""
    if "auth_tokens" not in st.session_state:
        return {"success": False, "message": "No active sessions"}
    
    if token not in st.session_state.auth_tokens:
        return {"success": False, "message": "Invalid token"}
    
    token_data = st.session_state.auth_tokens[token]
    if datetime.datetime.now() > token_data["expires"]:
        # Token has expired
        del st.session_state.auth_tokens[token]
        return {"success": False, "message": "Token expired"}
    
    return {"success": True, "username": token_data["username"]}

def logout(token):
    """Invalidate a token"""
    if "auth_tokens" in st.session_state and token in st.session_state.auth_tokens:
        del st.session_state.auth_tokens[token]
    return {"success": True}

def login_form():
    """Display a login form and handle authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.auth_token = None
    
    if not st.session_state.authenticated:
        st.title("Hotel Financial Dashboard")
        
        tab1, tab2 = st.tabs(["Login", "Help"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    result = check_credentials(username, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.username = result["username"]
                        st.session_state.auth_token = result["token"]
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            st.info("""
            ## Default Credentials
            - Username: admin
            - Password: admin
            
            Contact your administrator if you need access.
            """)
        
        return False
    else:
        # Add logout button to sidebar
        if st.sidebar.button("Logout"):
            logout(st.session_state.auth_token)
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.auth_token = None
            st.experimental_rerun()
        
        return True
