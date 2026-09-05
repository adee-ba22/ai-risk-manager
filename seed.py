import database as db
import auth
import ai_engine

def seed_database():
    """Seed sample users, initial login records, and enterprise risks."""
    db.init_db()

    # 1. Seed Demo Users if no users exist
    admin_user = db.get_user_by_email('admin@airiskmanager.com')
    if not admin_user:
        admin_user = db.create_user(
            name='John Security Admin',
            email='admin@airiskmanager.com',
            password_hash=auth.hash_password('admin123'),
            role='admin'
        )
        db.record_user_login(admin_user['id'], admin_user['name'], admin_user['email'], '127.0.0.1', 'Chrome / Windows')
        print("[Seed] Created Admin User: admin@airiskmanager.com / admin123")

    john_user = db.get_user_by_email('john@example.com')
    if not john_user:
        john_user = db.create_user(
            name='John Doe',
            email='john@example.com',
            password_hash=auth.hash_password('user123'),
            role='user'
        )
        db.record_user_login(john_user['id'], john_user['name'], john_user['email'], '127.0.0.1', 'Firefox / Windows')
        print("[Seed] Created Standard User: john@example.com / user123")

    sarah_user = db.get_user_by_email('sarah.analyst@example.com')
    if not sarah_user:
        sarah_user = db.create_user(
            name='Sarah Analyst',
            email='sarah.analyst@example.com',
            password_hash=auth.hash_password('user123'),
            role='user'
        )
        db.record_user_login(sarah_user['id'], sarah_user['name'], sarah_user['email'], '192.168.1.45', 'Edge / Windows')
        print("[Seed] Created Analyst User: sarah.analyst@example.com / user123")

    # 2. Seed Initial Risks if empty
    existing_risks = db.get_all_risks()
    if not existing_risks:
        admin_id = admin_user['id'] if admin_user else 1

        sample_risks = [
            {
                'title': 'Unencrypted Production SQL Customer Database',
                'description': 'Main customer Postgres database containing PII data is stored on unencrypted EBS volumes without active transparent data encryption.',
                'asset': 'Production Customer Database (DB-PROD-01)',
                'threat_type': 'Data Breach / Exposure',
                'likelihood': 4,
                'impact': 5,
                'existing_controls': 'Standard AWS IAM Security Groups, IP Whitelisting',
                'notes': 'Discovered during Q3 internal compliance scan.',
                'status': 'Open'
            },
            {
                'title': 'Phishing Vulnerability in HR & Finance Department',
                'description': 'Targeted spear-phishing campaigns could compromise credentials of payroll managers lacking hardware MFA keys.',
                'asset': 'Enterprise Google Workspace & HR Portal',
                'threat_type': 'Phishing / Social Engineering',
                'likelihood': 4,
                'impact': 4,
                'existing_controls': 'SMS Multi-Factor Authentication, Basic Spam Filtering',
                'notes': 'HR team reported 2 suspicious email attachments last week.',
                'status': 'In Progress'
            },
            {
                'title': 'Publicly Exposed AWS S3 Data Analytics Bucket',
                'description': 'Analytics export S3 bucket misconfigured with public read permissions exposing aggregated telemetry data.',
                'asset': 'AWS S3 Bucket (s3://corp-analytics-exports)',
                'threat_type': 'Misconfiguration / Cloud Security',
                'likelihood': 3,
                'impact': 4,
                'existing_controls': 'S3 Block Public Access toggle at root account level',
                'notes': 'Detected via cloud posture scanner alert.',
                'status': 'Open'
            },
            {
                'title': 'Ransomware Risk on Legacy Windows Workstations',
                'description': 'Unpatched Windows 10 endpoints in remote branch offices running outdated EDR signatures.',
                'asset': 'Branch Office Workstations (50+ PCs)',
                'threat_type': 'Ransomware / Malware',
                'likelihood': 3,
                'impact': 5,
                'existing_controls': 'Windows Defender Antivirus, Weekly WSUS updates',
                'notes': 'Pending remote OS patch rollout.',
                'status': 'Open'
            },
            {
                'title': 'Third-Party Node.js Package Supply Chain Vulnerability',
                'description': 'Outdated dependency in customer API gateway containing known Remote Code Execution (RCE) vulnerability (CVE-2025-2189).',
                'asset': 'Public API Gateway Microservice',
                'threat_type': 'Supply Chain / Third-Party Risk',
                'likelihood': 3,
                'impact': 3,
                'existing_controls': 'npm audit checks during manual release builds',
                'notes': 'Requires upgrading node module dependencies.',
                'status': 'In Progress'
            },
            {
                'title': 'Missing Multi-Factor Authentication on Internal Dev Wiki',
                'description': 'Confluence developer portal relies solely on single-factor password authentication.',
                'asset': 'Internal Developer Knowledge Base',
                'threat_type': 'Unauthorized Access',
                'likelihood': 2,
                'impact': 2,
                'existing_controls': 'Enforced single sign-on (SSO) with Okta MFA integration.',
                'notes': 'MFA successfully enforced across all developer accounts.',
                'status': 'Mitigated'
            }
        ]

        for r in sample_risks:
            ai_rec = ai_engine.generate_ai_recommendation(r)
            r.update(ai_rec)
            db.create_risk(r, admin_id)

        print(f"[Seed] Successfully seeded {len(sample_risks)} initial enterprise risks!")

if __name__ == '__main__':
    seed_database()
