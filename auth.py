import functools
import secrets
from flask import request, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import database as db

# In-memory session store mapping session token to user dict (also stored in Flask session)
SESSIONS = {}

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)

def create_session(user, ip_address='127.0.0.1', user_agent='Web'):
    token = secrets.token_hex(32)
    session_data = {
        'token': token,
        'user_id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role']
    }
    SESSIONS[token] = session_data
    db.record_user_login(user['id'], user['name'], user['email'], ip_address, user_agent)
    return token

def get_current_user():
    token = None
    # Check Authorization header: Bearer <token>
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    elif 'session_token' in session:
        token = session.get('session_token')
    
    if token and token in SESSIONS:
        user_data = SESSIONS[token]
        user = db.get_user_by_id(user_data['user_id'])
        if user:
            return user
    return None

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'error': 'Authentication required. Please sign in.',
                'code': 'UNAUTHORIZED'
            }), 401
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'error': 'Authentication required. Please sign in.',
                'code': 'UNAUTHORIZED'
            }), 401
        if user.get('role') != 'admin':
            return jsonify({
                'error': 'Access denied. Administrator privileges required.',
                'code': 'FORBIDDEN'
            }), 403
        g.user = user
        return f(*args, **kwargs)
    return decorated_function
