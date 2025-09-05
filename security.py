import re
import time
from collections import defaultdict
from urllib.parse import urlparse
from database import get_db_connection

# Simple rate limiting implementation
# In a production environment, you would use Redis or similar for distributed rate limiting
request_counts = defaultdict(list)

# List of known malicious domains (in a real application, this would be more comprehensive)
MALICIOUS_DOMAINS = {
    'malicious-site.com',
    'phishing-example.org',
    'fake-bank.net'
}

def is_rate_limited(ip_address, max_requests=10, time_window=60):
    """
    Check if an IP address is rate limited
    """
    current_time = time.time()
    
    # Remove requests outside the time window
    request_counts[ip_address] = [req_time for req_time in request_counts[ip_address] 
                                  if current_time - req_time < time_window]
    
    # Check if limit exceeded
    if len(request_counts[ip_address]) >= max_requests:
        return True
    
    # Add current request
    request_counts[ip_address].append(current_time)
    return False

def is_malicious_url(url):
    """
    Check if a URL is potentially malicious
    In production, this would integrate with services like VirusTotal
    """
    if not url:
        return False
    
    # Parse URL to extract domain
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Check against known malicious domains
    if domain in MALICIOUS_DOMAINS:
        return True
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'\b(?:union|select|insert|delete|update|drop|create|alter)\b',  # SQL injection keywords
        r'<script',  # Basic XSS detection
        r'\b(?:bitcoin|cryptocurrency|wallet)\b',  # Often associated with scam sites
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

def reset_rate_limit(ip_address):
    """
    Reset rate limit for an IP address (useful for testing)
    """
    if ip_address in request_counts:
        del request_counts[ip_address]