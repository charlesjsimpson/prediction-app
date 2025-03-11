import json
import hashlib
import secrets
import datetime
from pathlib import Path

# Create database directory if it doesn't exist
database_dir = Path("database")
database_dir.mkdir(exist_ok=True)

# Path to user database file
USER_DB_PATH = database_dir / "users.json"
TOKEN_DB_PATH = database_dir / "tokens.json"

def _hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def _generate_token():
    """Generate a secure random token"""
    return secrets.token_hex(32)

def _load_user_db():
    """Load the user database from file"""
    if not USER_DB_PATH.exists():
        return {}
    
    try:
        with open(USER_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_user_db(user_db):
    """Save the user database to file"""
    with open(USER_DB_PATH, 'w') as f:
        json.dump(user_db, f, indent=4)

def _load_token_db():
    """Load the token database from file"""
    if not TOKEN_DB_PATH.exists():
        return {}
    
    try:
        with open(TOKEN_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_token_db(token_db):
    """Save the token database to file"""
    with open(TOKEN_DB_PATH, 'w') as f:
        json.dump(token_db, f, indent=4)

def create_user(username, password):
    """
    Create a new user
    
    Parameters:
    -----------
    username : str
        Username for the new account
    password : str
        Password for the new account
    
    Returns:
    --------
    dict
        Result of the operation with success flag and message
    """
    # Load current user database
    user_db = _load_user_db()
    
    # Check if username already exists
    if username in user_db:
        return {"success": False, "message": "Username already exists"}
    
    # Create new user entry
    user_db[username] = {
        "password_hash": _hash_password(password),
        "created_at": datetime.datetime.now().isoformat()
    }
    
    # Save updated user database
    _save_user_db(user_db)
    
    return {"success": True, "message": "User created successfully"}

def check_authentication(username, password=None, token=None):
    """
    Check user authentication using either username/password or token
    
    Parameters:
    -----------
    username : str
        Username for authentication
    password : str, optional
        Password for authentication
    token : str, optional
        Authentication token
    
    Returns:
    --------
    dict
        Authentication result with success flag, username, and token
    """
    # If token is provided, verify token
    if token:
        token_db = _load_token_db()
        if token in token_db:
            # Check if token is expired
            expiry = datetime.datetime.fromisoformat(token_db[token]["expires_at"])
            if expiry > datetime.datetime.now():
                return {
                    "success": True,
                    "username": token_db[token]["username"],
                    "token": token
                }
            else:
                # Remove expired token
                del token_db[token]
                _save_token_db(token_db)
        
        return {"success": False, "message": "Invalid or expired token"}
    
    # If username/password provided, verify credentials
    if username and password:
        user_db = _load_user_db()
        
        if username in user_db and user_db[username]["password_hash"] == _hash_password(password):
            # Generate new token
            token = _generate_token()
            
            # Save token to database
            token_db = _load_token_db()
            token_db[token] = {
                "username": username,
                "created_at": datetime.datetime.now().isoformat(),
                "expires_at": (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
            }
            _save_token_db(token_db)
            
            return {
                "success": True,
                "username": username,
                "token": token
            }
    
    return {"success": False, "message": "Invalid username or password"}

def logout_user(token=None):
    """
    Logout a user by invalidating their token
    
    Parameters:
    -----------
    token : str, optional
        Token to invalidate
    
    Returns:
    --------
    dict
        Result of the operation with success flag
    """
    if token:
        token_db = _load_token_db()
        if token in token_db:
            del token_db[token]
            _save_token_db(token_db)
    
    return {"success": True}

# Initialize with a default admin user if no users exist
def initialize_default_user():
    user_db = _load_user_db()
    if not user_db:
        create_user("admin", "admin123")

# Initialize default user
initialize_default_user()
