from flask import Flask, request, redirect, jsonify, render_template, url_for, flash, session
from flask_caching import Cache
import qrcode
import io
import base64
from urllib.parse import urlparse
from database import init_db, get_db_connection
from utils import generate_short_code, is_valid_url, sanitize_url, hash_password, verify_password
from security import is_rate_limited, is_malicious_url
# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configure caching with timeout
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes cache timeout
})

# Initialize database
init_db()

@app.route('/')
def index():
    """Render the homepage"""
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Create a new short URL"""
    data = request.get_json() if request.is_json else request.form
    
    original_url = data.get('url')
    custom_code = data.get('custom_code')
    
    # Get client IP for rate limiting
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    
    # Check for rate limiting
    if is_rate_limited(client_ip):
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    
    # Validate URL
    if not original_url or not is_valid_url(original_url):
        # Try to sanitize the URL (add https:// if missing)
        sanitized = sanitize_url(original_url)
        if not sanitized or not is_valid_url(sanitized):
            return jsonify({'error': 'Invalid URL provided'}), 400
        original_url = sanitized
    
    # Check for malicious URL
    if is_malicious_url(original_url):
        return jsonify({'error': 'Malicious URL detected'}), 400
    
    # Generate short code
    short_code = custom_code if custom_code else generate_short_code()
    
    # Check if custom code already exists
    if custom_code:
        with get_db_connection() as conn:
            existing = conn.execute('SELECT id FROM urls WHERE short_code = ?', (custom_code,)).fetchone()
            if existing:
                return jsonify({'error': 'Custom short code already exists'}), 400
    
    # Insert into database
    with get_db_connection() as conn:
        try:
            conn.execute(
                'INSERT INTO urls (original_url, short_code) VALUES (?, ?)',
                (original_url, short_code)
            )
            conn.commit()
            url_record = conn.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,)).fetchone()
            if url_record:
                url_id = url_record['id']
            else:
                return jsonify({'error': 'Failed to retrieve URL after creation'}), 500
        except Exception as e:
            return jsonify({'error': 'Failed to create short URL'}), 500
    
    # Generate short URL
    short_url = request.host_url + short_code
    
    # Cache the URL mapping with explicit timeout
    cache.set(short_code, original_url, timeout=300)  # 5 minutes cache timeout
    
    return jsonify({
        'short_url': short_url,
        'short_code': short_code,
        'original_url': original_url
    })

@app.route('/<short_code>')
def redirect_url(short_code):
    """Redirect to the original URL and track clicks"""
    # Check cache first
    original_url = cache.get(short_code)
    
    if not original_url:
        # If not in cache, check database
        with get_db_connection() as conn:
            url_record = conn.execute('SELECT * FROM urls WHERE short_code = ? AND is_active = TRUE', (short_code,)).fetchone()
        
        if not url_record:
            flash('Short URL not found or is inactive')
            return redirect(url_for('index'))
        
        original_url = url_record['original_url']
        
        # Add to cache for future requests with explicit timeout
        cache.set(short_code, original_url, timeout=300)  # 5 minutes cache timeout
    
    # Track click in analytics
    track_click(short_code)
    
    return redirect(original_url)

@app.route('/preview/<short_code>')
def preview_url(short_code):
    """Preview the original URL without redirecting"""
    with get_db_connection() as conn:
        url_record = conn.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,)).fetchone()
    
    if not url_record:
        return jsonify({'error': 'Short URL not found'}), 404
    
    return jsonify({'original_url': url_record['original_url']})

@app.route('/qr/<short_code>')
def generate_qr(short_code):
    """Generate QR code for a short URL"""
    short_url = request.host_url + short_code
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(short_url)
    qr.make(fit=True)
    
    # Generate image
    img = qr.make_image(fill='black', back_color='white')
    
    # Convert to base64 for easy transfer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    return jsonify({'qr_code': img_str})

def track_click(short_code):
    """Track a click on a short URL"""
    # Get client information
    ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    user_agent = request.headers.get('User-Agent')
    referer = request.headers.get('Referer')
    
    # Get URL ID from database
    with get_db_connection() as conn:
        url_record = conn.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,)).fetchone()
    
    if url_record:
        url_id = url_record['id']
        
        # Increment click count and record analytics data
        with get_db_connection() as conn:
            # Increment click count
            conn.execute('UPDATE urls SET clicks = clicks + 1 WHERE id = ?', (url_id,))
            conn.commit()
            
            # Record analytics data
            conn.execute(
                'INSERT INTO analytics (url_id, ip_address, user_agent, referer) VALUES (?, ?, ?, ?)',
                (url_id, ip_address, user_agent, referer)
            )
            conn.commit()

@app.route('/admin')
def admin_panel():
    """Render the admin panel"""
    return render_template('admin.html')

@app.route('/admin/urls')
def admin_urls():
    """Get all URLs for admin management"""
    with get_db_connection() as conn:
        urls = conn.execute('SELECT * FROM urls ORDER BY created_at DESC').fetchall()
    
    # Convert to list of dictionaries
    urls_list = []
    for url in urls:
        urls_list.append({
            'id': url['id'],
            'original_url': url['original_url'],
            'short_code': url['short_code'],
            'created_at': url['created_at'],
            'clicks': url['clicks'],
            'is_active': url['is_active']
        })
    
    return jsonify(urls_list)

@app.route('/admin/urls/<int:url_id>/toggle', methods=['POST'])
def toggle_url(url_id):
    """Toggle URL active status"""
    with get_db_connection() as conn:
        url = conn.execute('SELECT is_active, short_code FROM urls WHERE id = ?', (url_id,)).fetchone()
    
    if not url:
        return jsonify({'error': 'URL not found'}), 404
    
    # Toggle status
    new_status = not url['is_active']
    with get_db_connection() as conn:
        conn.execute('UPDATE urls SET is_active = ? WHERE id = ?', (new_status, url_id))
        conn.commit()
    
    # Clear cache if URL is being disabled
    if not new_status:
        cache.delete(url['short_code'])
    
    return jsonify({'success': True, 'is_active': new_status})

@app.route('/admin/urls/<int:url_id>/delete', methods=['POST'])
def delete_url(url_id):
    """Delete a URL"""
    with get_db_connection() as conn:
        short_code = conn.execute('SELECT short_code FROM urls WHERE id = ?', (url_id,)).fetchone()
    
    if not short_code:
        return jsonify({'error': 'URL not found'}), 404
    
    # Delete URL and related analytics
    with get_db_connection() as conn:
        conn.execute('DELETE FROM analytics WHERE url_id = ?', (url_id,))
        conn.execute('DELETE FROM urls WHERE id = ?', (url_id,))
        conn.commit()
    
    # Clear cache
    cache.delete(short_code['short_code'])
    
    return jsonify({'success': True})

@app.route('/admin/users')
def admin_users():
    """Get all users for admin management"""
    with get_db_connection() as conn:
        users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    
    # Convert to list of dictionaries
    users_list = []
    for user in users:
        users_list.append({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'is_admin': user['is_admin']
        })
    
    return jsonify(users_list)

@app.route('/admin/dashboard')
def admin_dashboard():
    """Render the analytics dashboard"""
    return render_template('dashboard.html')

@app.route('/admin/dashboard/stats')
def dashboard_stats():
    """Get statistics data for the dashboard"""
    with get_db_connection() as conn:
        # Get total URLs
        total_urls = conn.execute('SELECT COUNT(*) as count FROM urls').fetchone()['count']
        
        # Get total clicks
        total_clicks = conn.execute('SELECT SUM(clicks) as sum FROM urls').fetchone()['sum'] or 0
        
        # Get active URLs
        active_urls = conn.execute('SELECT COUNT(*) as count FROM urls WHERE is_active = TRUE').fetchone()['count']
        
        # Get top country by clicks
        top_country = conn.execute('''
            SELECT country, COUNT(*) as count
            FROM analytics
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 1
        ''').fetchone()
    
    top_country_name = top_country['country'] if top_country else 'Unknown'
    
    return jsonify({
        'total_urls': total_urls,
        'total_clicks': total_clicks,
        'active_urls': active_urls,
        'top_country': top_country_name
    })

@app.route('/admin/dashboard/recent')
def recent_activity():
    """Get recent activity data for the dashboard"""
    with get_db_connection() as conn:
        # Get recent clicks (last 10)
        recent_clicks = conn.execute('''
            SELECT a.timestamp, a.ip_address, a.country, u.short_code, u.original_url
            FROM analytics a
            JOIN urls u ON a.url_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT 10
        ''').fetchall()
    
    # Convert to list of dictionaries
    activities = []
    for click in recent_clicks:
        activities.append({
            'timestamp': click['timestamp'],
            'ip_address': click['ip_address'],
            'country': click['country'] or 'Unknown',
            'short_code': click['short_code'],
            'original_url': click['original_url']
        })
    
    return jsonify(activities)

@app.route('/admin/dashboard/chart/clicks-over-time')
def clicks_over_time_chart_data():
    """Get clicks over time data for the chart"""
    with get_db_connection() as conn:
        # Get clicks grouped by day for the last 7 days
        chart_data = conn.execute('''
            SELECT DATE(timestamp) as day, COUNT(*) as clicks
            FROM analytics
            WHERE timestamp >= DATE('now', '-7 days')
            GROUP BY day
            ORDER BY day
        ''').fetchall()
    
    labels = [row['day'] for row in chart_data]
    clicks = [row['clicks'] for row in chart_data]
    
    return jsonify({
        'labels': labels,
        'clicks': clicks
    })

@app.route('/admin/dashboard/chart/geographic-distribution')
def geographic_distribution_chart_data():
    """Get geographic distribution data for the chart"""
    with get_db_connection() as conn:
        # Get clicks by country
        chart_data = conn.execute('''
            SELECT country, COUNT(*) as clicks
            FROM analytics
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY clicks DESC
            LIMIT 10
        ''').fetchall()
    
    labels = [row['country'] for row in chart_data]
    clicks = [row['clicks'] for row in chart_data]
    
    return jsonify({
        'labels': labels,
        'clicks': clicks
    })

@app.route('/admin/dashboard/chart/top-urls')
def top_urls_chart_data():
    """Get top URLs by clicks data for the chart"""
    with get_db_connection() as conn:
        # Get top URLs by clicks
        chart_data = conn.execute('''
            SELECT short_code, clicks
            FROM urls
            WHERE clicks > 0
            ORDER BY clicks DESC
            LIMIT 10
        ''').fetchall()
    
    labels = [row['short_code'] for row in chart_data]
    clicks = [row['clicks'] for row in chart_data]
    
    return jsonify({
        'labels': labels,
        'clicks': clicks
    })

@app.route('/admin/dashboard/chart/device-types')
def device_types_chart_data():
    """Get device types data for the chart"""
    with get_db_connection() as conn:
        # Get device types from user agent strings
        chart_data = conn.execute('''
            SELECT user_agent,
                   COUNT(*) as clicks
            FROM analytics
            GROUP BY user_agent
            ORDER BY clicks DESC
        ''').fetchall()
    
    # Categorize devices (simplified)
    device_counts = {'Desktop': 0, 'Mobile': 0, 'Tablet': 0, 'Other': 0}
    
    for row in chart_data:
        user_agent = row['user_agent']
        clicks = row['clicks']
        
        if user_agent:
            if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                device_counts['Mobile'] += clicks
            elif 'Tablet' in user_agent or 'iPad' in user_agent:
                device_counts['Tablet'] += clicks
            else:
                device_counts['Desktop'] += clicks
        else:
            device_counts['Other'] += clicks
    
    labels = list(device_counts.keys())
    clicks = list(device_counts.values())
    
    return jsonify({
        'labels': labels,
        'clicks': clicks
    })

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Authenticate admin user"""
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Get user from database
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['is_admin'] = user['is_admin']
    
    return jsonify({'success': True, 'username': user['username'], 'is_admin': user['is_admin']})

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Logout admin user"""
    session.clear()
    return jsonify({'success': True})

@app.route('/admin/session', methods=['GET'])
def admin_session():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'username': session['username'],
            'is_admin': session['is_admin']
        })
    else:
        return jsonify({'authenticated': False}), 401

if __name__ == '__main__':
    app.run(debug=True)