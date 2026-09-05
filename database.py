import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'risk_manager.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialize SQLite database with schema."""
    conn = get_db()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def compute_severity(likelihood, impact):
    """Calculate risk score and severity level."""
    score = likelihood * impact
    if score <= 4:
        severity = "Low"
    elif score <= 9:
        severity = "Medium"
    elif score <= 15:
        severity = "High"
    else:
        severity = "Critical"
    return score, severity

# User helpers
def create_user(name, email, password_hash, role='user'):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role, status) VALUES (?, ?, ?, ?, 'Active')",
            (name, email.lower().strip(), password_hash, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.lower().strip(),)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def record_user_login(user_id, name, email, ip_address='127.0.0.1', user_agent='Web Browser'):
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Update last login on user
    conn.execute("UPDATE users SET last_login = ?, status = 'Active' WHERE id = ?", (now, user_id))
    # Record session entry in user_sessions table
    conn.execute(
        "INSERT INTO user_sessions (user_id, name, email, sign_in_time, ip_address, user_agent, status) VALUES (?, ?, ?, ?, ?, ?, 'Active')",
        (user_id, name, email, now, ip_address, user_agent)
    )
    conn.commit()
    conn.close()

def get_all_user_sessions():
    """Retrieve sign-in logs for Admin Dashboard."""
    conn = get_db()
    sessions = conn.execute("""
        SELECT s.id, s.user_id, s.name, s.email, s.sign_in_time, s.ip_address, s.status, u.role
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.sign_in_time DESC
    """).fetchall()
    conn.close()
    return [dict(s) for s in sessions]

def get_all_users():
    """Get all registered users for Admin panel."""
    conn = get_db()
    users = conn.execute("""
        SELECT u.id, u.name, u.email, u.role, u.status, u.created_at, u.last_login,
        (SELECT COUNT(*) FROM user_sessions s WHERE s.user_id = u.id) as login_count
        FROM users u
        ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(u) for u in users]

# Risk helpers
def get_all_risks(severity_filter=None, status_filter=None, search_query=None):
    conn = get_db()
    query = """
        SELECT r.*, u.name as creator_name
        FROM risks r
        JOIN users u ON r.created_by = u.id
        WHERE 1=1
    """
    params = []

    if severity_filter and severity_filter != 'All':
        query += " AND r.severity = ?"
        params.append(severity_filter)

    if status_filter and status_filter != 'All':
        query += " AND r.status = ?"
        params.append(status_filter)

    if search_query:
        query += " AND (r.title LIKE ? OR r.asset LIKE ? OR r.threat_type LIKE ? OR r.description LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    query += " ORDER BY r.risk_score DESC, r.created_at DESC"
    risks = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in risks]

def get_risk_by_id(risk_id):
    conn = get_db()
    risk = conn.execute("""
        SELECT r.*, u.name as creator_name, u.email as creator_email
        FROM risks r
        JOIN users u ON r.created_by = u.id
        WHERE r.id = ?
    """, (risk_id,)).fetchone()
    conn.close()
    return dict(risk) if risk else None

def create_risk(risk_data, user_id):
    score, severity = compute_severity(int(risk_data['likelihood']), int(risk_data['impact']))
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO risks (
            title, description, asset, threat_type, likelihood, impact,
            risk_score, severity, existing_controls, notes, status,
            ai_explanation, ai_mitigation, ai_priority, ai_controls,
            created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        risk_data['title'],
        risk_data['description'],
        risk_data['asset'],
        risk_data['threat_type'],
        int(risk_data['likelihood']),
        int(risk_data['impact']),
        score,
        severity,
        risk_data.get('existing_controls', ''),
        risk_data.get('notes', ''),
        risk_data.get('status', 'Open'),
        risk_data.get('ai_explanation', ''),
        risk_data.get('ai_mitigation', ''),
        risk_data.get('ai_priority', severity),
        risk_data.get('ai_controls', ''),
        user_id,
        now,
        now
    ))
    conn.commit()
    risk_id = cursor.lastrowid
    conn.close()
    return get_risk_by_id(risk_id)

def update_risk(risk_id, risk_data):
    score, severity = compute_severity(int(risk_data['likelihood']), int(risk_data['impact']))
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        UPDATE risks SET
            title = ?, description = ?, asset = ?, threat_type = ?,
            likelihood = ?, impact = ?, risk_score = ?, severity = ?,
            existing_controls = ?, notes = ?, status = ?,
            ai_explanation = ?, ai_mitigation = ?, ai_priority = ?, ai_controls = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        risk_data['title'],
        risk_data['description'],
        risk_data['asset'],
        risk_data['threat_type'],
        int(risk_data['likelihood']),
        int(risk_data['impact']),
        score,
        severity,
        risk_data.get('existing_controls', ''),
        risk_data.get('notes', ''),
        risk_data.get('status', 'Open'),
        risk_data.get('ai_explanation', ''),
        risk_data.get('ai_mitigation', ''),
        risk_data.get('ai_priority', severity),
        risk_data.get('ai_controls', ''),
        now,
        risk_id
    ))
    conn.commit()
    conn.close()
    return get_risk_by_id(risk_id)

def update_risk_status(risk_id, status):
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE risks SET status = ?, updated_at = ? WHERE id = ?", (status, now, risk_id))
    conn.commit()
    conn.close()
    return get_risk_by_id(risk_id)

def delete_risk(risk_id):
    conn = get_db()
    conn.execute("DELETE FROM risks WHERE id = ?", (risk_id,))
    conn.commit()
    conn.close()
    return True

def get_dashboard_metrics():
    """Retrieve comprehensive statistical metrics for dashboard and charts."""
    conn = get_db()
    total_risks = conn.execute("SELECT COUNT(*) FROM risks").fetchone()[0]
    critical_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'Critical'").fetchone()[0]
    high_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'High'").fetchone()[0]
    medium_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'Medium'").fetchone()[0]
    low_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE severity = 'Low'").fetchone()[0]

    open_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE status = 'Open'").fetchone()[0]
    in_progress_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE status = 'In Progress'").fetchone()[0]
    mitigated_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE status = 'Mitigated'").fetchone()[0]

    avg_score_row = conn.execute("SELECT AVG(risk_score) FROM risks").fetchone()[0]
    avg_score = round(avg_score_row, 1) if avg_score_row is not None else 0.0

    # Determine overall risk score & level
    if avg_score >= 18 or critical_risks > 2:
        overall_level = "Critical"
    elif avg_score >= 12 or high_risks > 3:
        overall_level = "High"
    elif avg_score >= 6 or medium_risks > 4:
        overall_level = "Medium"
    else:
        overall_level = "Low"

    # Severity distribution dictionary
    severity_dist = {
        'Critical': critical_risks,
        'High': high_risks,
        'Medium': medium_risks,
        'Low': low_risks
    }

    # Status distribution
    status_dist = {
        'Open': open_risks,
        'In Progress': in_progress_risks,
        'Mitigated': mitigated_risks
    }

    # Recent risks
    recent_risks = conn.execute("""
        SELECT r.*, u.name as creator_name
        FROM risks r
        JOIN users u ON r.created_by = u.id
        ORDER BY r.created_at DESC LIMIT 5
    """).fetchall()

    # Top cybersecurity risks (highest risk score)
    top_risks = conn.execute("""
        SELECT title, asset, threat_type, risk_score, severity, status
        FROM risks
        ORDER BY risk_score DESC LIMIT 5
    """).fetchall()

    conn.close()

    return {
        'total_risks': total_risks,
        'critical_risks': critical_risks,
        'high_risks': high_risks,
        'medium_risks': medium_risks,
        'low_risks': low_risks,
        'open_risks': open_risks,
        'in_progress_risks': in_progress_risks,
        'mitigated_risks': mitigated_risks,
        'avg_risk_score': avg_score,
        'overall_risk_level': overall_level,
        'severity_distribution': severity_dist,
        'status_distribution': status_dist,
        'recent_risks': [dict(r) for r in recent_risks],
        'top_risks': [dict(r) for r in top_risks]
    }

# Settings helpers
def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default

def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
