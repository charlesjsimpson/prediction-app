import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st

# Add the project root to the path to ensure imports work correctly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Create logs directory if it doesn't exist
logs_dir = os.path.join(root_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure the logging system
def setup_logger(name=None):
    """
    Set up and configure a logger with file and console handlers.
    
    Args:
        name (str, optional): Name for the logger. If None, uses the root logger.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get or create logger
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()
    
    # Only configure if it hasn't been configured yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        # Create file handler with date in filename
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'hotel_dashboard_{current_date}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Function to log user actions with Streamlit
def log_action(action, user=None, details=None, level='info'):
    """
    Log a user action in the application.
    
    Args:
        action (str): The action being performed
        user (str, optional): Username of the current user
        details (str, optional): Additional details about the action
        level (str, optional): Log level ('debug', 'info', 'warning', 'error', 'critical')
    """
    logger = setup_logger('hotel_dashboard')
    
    # Get username from session state if not provided
    if user is None and 'username' in st.session_state:
        user = st.session_state.username
    
    # Create log message
    message = f"Action: {action}"
    if user:
        message = f"User: {user} - {message}"
    if details:
        message = f"{message} - Details: {details}"
    
    # Log at the appropriate level
    if level == 'debug':
        logger.debug(message)
    elif level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'critical':
        logger.critical(message)
    else:
        logger.info(message)  # Default to info level

# Function to log page access
def log_page_access(page_name):
    """
    Log when a user accesses a specific page.
    
    Args:
        page_name (str): Name of the page being accessed
    """
    log_action(f"Accessed page: {page_name}")

# Function to log data operations
def log_data_operation(operation, dataset=None, details=None):
    """
    Log data operations like loading, saving, or modifying data.
    
    Args:
        operation (str): Type of operation (e.g., 'load', 'save', 'modify')
        dataset (str, optional): Name of the dataset being operated on
        details (str, optional): Additional details about the operation
    """
    action = f"Data {operation}"
    if dataset:
        action = f"{action} - Dataset: {dataset}"
    log_action(action, details=details)

# Function to log errors
def log_error(error_message, exception=None):
    """
    Log an error that occurred in the application.
    
    Args:
        error_message (str): Description of the error
        exception (Exception, optional): The exception that was raised
    """
    details = str(exception) if exception else None
    log_action(error_message, details=details, level='error')
