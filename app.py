import os
from flask import Flask, request, jsonify, render_template, send_file, session
from flask_cors import CORS
import io

import database as db
import auth
import ai_engine
import report_generator

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'ai-risk-manager-secret-key-2026-super-secure')
CORS(app)

# Ensure database is initialized on startup
with app.app_context():
    db.init_db()

@app.route('/')
def index():
    """Serve SPA container."""
    return render_template('index.html')

# ================= AUTHENTICATION ENDPOINTS =================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    existing_user = db.get_user_by_email(email)
    if existing_user:
        return jsonify({'error': 'An account with this email address already exists.'}), 400

    password_hash = auth.hash_password(password)
    user = db.create_user(name, email, password_hash, role)
    if not user:
        return jsonify({'error': 'Failed to create user account.'}), 500

    # Auto sign-in upon registration
    token = auth.create_session(user, request.remote_addr, request.headers.get('User-Agent', 'Browser'))
    session['session_token'] = token

    return jsonify({
        'message': 'Account created successfully!',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role']
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = db.get_user_by_email(email)
    if not user or not auth.verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid email address or password.'}), 401

    token = auth.create_session(user, request.remote_addr, request.headers.get('User-Agent', 'Browser'))
    session['session_token'] = token

    return jsonify({
        'message': 'Signed in successfully!',
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'last_login': user['last_login']
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('session_token', None)
    return jsonify({'message': 'Logged out successfully.'}), 200

@app.route('/api/auth/me', methods=['GET'])
@auth.login_required
def get_me():
    user = auth.get_current_user()
    return jsonify({
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
        'status': user['status'],
        'created_at': user['created_at'],
        'last_login': user['last_login']
    }), 200

# ================= ADMIN USER TRACKING ENDPOINTS =================

@app.route('/api/admin/users', methods=['GET'])
@auth.admin_required
def admin_get_users():
    """Retrieve all user sign-in logs and user directory. Restricted to Admin."""
    sessions = db.get_all_user_sessions()
    all_users = db.get_all_users()
    return jsonify({
        'sessions': sessions,
        'users': all_users
    }), 200

# ================= RISK MANAGEMENT ENDPOINTS =================

@app.route('/api/risks', methods=['GET'])
@auth.login_required
def get_risks():
    severity = request.args.get('severity')
    status_filter = request.args.get('status')
    search = request.args.get('search')
    risks = db.get_all_risks(severity, status_filter, search)
    return jsonify(risks), 200

@app.route('/api/risks/<int:risk_id>', methods=['GET'])
@auth.login_required
def get_risk(risk_id):
    risk = db.get_risk_by_id(risk_id)
    if not risk:
        return jsonify({'error': 'Risk record not found.'}), 404
    return jsonify(risk), 200

@app.route('/api/risks/recommend', methods=['POST'])
@auth.login_required
def preview_ai_recommendation():
    data = request.json or {}
    rec = ai_engine.generate_ai_recommendation(data)
    return jsonify(rec), 200

@app.route('/api/risks', methods=['POST'])
@auth.login_required
def create_risk_route():
    data = request.json or {}
    user = auth.get_current_user()

    required_fields = ['title', 'description', 'asset', 'threat_type', 'likelihood', 'impact']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f"Field '{field}' is required."}), 400

    # Generate AI recommendation if not provided
    if not data.get('ai_explanation'):
        ai_rec = ai_engine.generate_ai_recommendation(data)
        data.update(ai_rec)

    new_risk = db.create_risk(data, user['id'])
    return jsonify(new_risk), 201

@app.route('/api/risks/<int:risk_id>', methods=['PUT'])
@auth.login_required
def update_risk_route(risk_id):
    existing = db.get_risk_by_id(risk_id)
    if not existing:
        return jsonify({'error': 'Risk record not found.'}), 404

    data = request.json or {}
    if not data.get('ai_explanation'):
        ai_rec = ai_engine.generate_ai_recommendation(data)
        data.update(ai_rec)

    updated = db.update_risk(risk_id, data)
    return jsonify(updated), 200

@app.route('/api/risks/<int:risk_id>/status', methods=['PATCH'])
@auth.login_required
def patch_risk_status(risk_id):
    existing = db.get_risk_by_id(risk_id)
    if not existing:
        return jsonify({'error': 'Risk record not found.'}), 404

    data = request.json or {}
    new_status = data.get('status')
    if new_status not in ['Open', 'In Progress', 'Mitigated']:
        return jsonify({'error': 'Invalid status. Must be Open, In Progress, or Mitigated.'}), 400

    updated = db.update_risk_status(risk_id, new_status)
    return jsonify(updated), 200

@app.route('/api/risks/<int:risk_id>', methods=['DELETE'])
@auth.login_required
def delete_risk_route(risk_id):
    existing = db.get_risk_by_id(risk_id)
    if not existing:
        return jsonify({'error': 'Risk record not found.'}), 404

    db.delete_risk(risk_id)
    return jsonify({'message': 'Risk record deleted successfully.'}), 200

# ================= DASHBOARD & METRICS ENDPOINTS =================

@app.route('/api/dashboard/stats', methods=['GET'])
@auth.login_required
def get_dashboard_stats():
    metrics = db.get_dashboard_metrics()
    return jsonify(metrics), 200

# ================= REPORT GENERATION ENDPOINTS =================

@app.route('/api/reports/pdf', methods=['GET', 'POST'])
@auth.login_required
def download_pdf_report():
    user = auth.get_current_user()
    org_name = request.args.get('organization', 'Enterprise Cybersecurity Ops')
    pdf_bytes = report_generator.generate_pdf_report(org_name, user['name'])

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"AI_Risk_Assessment_Report_{user['name'].replace(' ', '_')}.pdf"
    )

# ================= SETTINGS ENDPOINTS =================

@app.route('/api/settings', methods=['GET', 'PUT'])
@auth.login_required
def manage_settings():
    if request.method == 'GET':
        gemini_key = db.get_setting('gemini_api_key', '')
        # Mask key for privacy
        masked_key = (gemini_key[:4] + '...' + gemini_key[-4:]) if len(gemini_key) > 8 else ''
        return jsonify({
            'has_gemini_key': bool(gemini_key),
            'masked_gemini_key': masked_key
        }), 200
    else:
        data = request.json or {}
        if 'gemini_api_key' in data:
            db.set_setting('gemini_api_key', data['gemini_api_key'].strip())
        return jsonify({'message': 'Settings updated successfully.'}), 200

if __name__ == '__main__':
    # Pre-seed demo users & initial risks if DB is empty
    import seed
    seed.seed_database()

    print("=========================================================")
    print("  AI RISK MANAGER - Enterprise Cybersecurity Platform    ")
    print("  Server running on http://127.0.0.1:5000               ")
    print("=========================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)
