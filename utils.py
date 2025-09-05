import re
import string
import random
import validators
from urllib.parse import urlparse

# Base62 characters (0-9, a-z, A-Z)
BASE62_CHARS = string.ascii_letters + string.digits

def generate_short_code(length=6):
    """
    Generate a random Base62 short code of specified length
    """
    return ''.join(random.choice(BASE62_CHARS) for _ in range(length))

def is_valid_url(url):
    """
    Validate if the provided string is a valid URL
    """
    if not url:
        return False
    
    # Check if it's a valid URL using the validators library
    if not validators.url(url):
        return False
    
    # Additional check to ensure it has a proper scheme and netloc
    parsed = urlparse(url)
    return bool(parsed.scheme) and bool(parsed.netloc)

def sanitize_url(url):
    """
    Ensure URL has proper scheme (default to https)
    """
    if not url:
        return None
    
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'https://' + url
    
    return url

def get_url_domain(url):
    """
    Extract domain from URL
    """
    if not url:
        return None
    
    parsed = urlparse(url)
    return parsed.netloc
import bcrypt

def hash_password(password):
    """
    Hash a password using bcrypt
    """
    # Convert password to bytes if it's not already
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    
    # Return hashed password as string
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """
    Verify a password against its hashed version using bcrypt
    """
    # Convert password to bytes if it's not already
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    # Convert hashed password to bytes if it's not already
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    # Verify password
    return bcrypt.checkpw(password, hashed_password)