import unittest
import os
import json
import database as db
import auth
import ai_engine

class AIRiskManagerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(db.DB_PATH):
            try:
                os.remove(db.DB_PATH)
            except Exception:
                pass
        db.init_db()
        import seed
        seed.seed_database()

        from app import app
        app.testing = True
        cls.client = app.test_client()

    def test_01_user_authentication_flow(self):
        """Test sign up, login, and token authentication."""
        reg_payload = {
            'name': 'Test Assessor',
            'email': 'assessor@enterprise.com',
            'password': 'password123',
            'role': 'user'
        }
        res = self.client.post('/api/auth/register', data=json.dumps(reg_payload), content_type='application/json')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'assessor@enterprise.com')

        login_payload = {
            'email': 'assessor@enterprise.com',
            'password': 'password123'
        }
        res = self.client.post('/api/auth/login', data=json.dumps(login_payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        token = json.loads(res.data)['token']

        res = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['name'], 'Test Assessor')

    def test_02_rbac_admin_user_tracking(self):
        """Test RBAC protection on Admin User Tracking view."""
        res = self.client.post('/api/auth/login', data=json.dumps({'email': 'john@example.com', 'password': 'user123'}), content_type='application/json')
        user_token = json.loads(res.data)['token']

        res = self.client.get('/api/admin/users', headers={'Authorization': f'Bearer {user_token}'})
        self.assertEqual(res.status_code, 403)

        res = self.client.post('/api/auth/login', data=json.dumps({'email': 'admin@airiskmanager.com', 'password': 'admin123'}), content_type='application/json')
        admin_token = json.loads(res.data)['token']

        res = self.client.get('/api/admin/users', headers={'Authorization': f'Bearer {admin_token}'})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('sessions', data)
        self.assertIn('users', data)
        self.assertGreater(len(data['sessions']), 0)

    def test_03_risk_score_calculation_and_crud(self):
        """Test Likelihood x Impact score calculation and Risk CRUD operations."""
        res = self.client.post('/api/auth/login', data=json.dumps({'email': 'admin@airiskmanager.com', 'password': 'admin123'}), content_type='application/json')
        token = json.loads(res.data)['token']
        headers = {'Authorization': f'Bearer {token}'}

        risk_data = {
            'title': 'Test Ransomware Threat',
            'description': 'Suspicious lateral movement activity detected in endpoint segment.',
            'asset': 'Internal Domain Controllers',
            'threat_type': 'Ransomware / Malware',
            'likelihood': 4,
            'impact': 5,
            'existing_controls': 'Windows Defender'
        }
        res = self.client.post('/api/risks', data=json.dumps(risk_data), content_type='application/json', headers=headers)
        self.assertEqual(res.status_code, 201)
        created = json.loads(res.data)
        self.assertEqual(created['risk_score'], 20)
        self.assertEqual(created['severity'], 'Critical')
        self.assertIn('ai_explanation', created)

        risk_id = created['id']

        res = self.client.patch(f'/api/risks/{risk_id}/status', data=json.dumps({'status': 'Mitigated'}), content_type='application/json', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['status'], 'Mitigated')

        res = self.client.delete(f'/api/risks/{risk_id}', headers=headers)
        self.assertEqual(res.status_code, 200)

    def test_04_ai_rule_engine_fallback(self):
        """Test AI rule-based recommendation generator output."""
        risk_data = {
            'title': 'Phishing HR attack',
            'description': 'Emails asking for payroll update.',
            'asset': 'HR Portal',
            'threat_type': 'Phishing / Social Engineering',
            'likelihood': 4,
            'impact': 4
        }
        rec = ai_engine.generate_rule_based_recommendation(risk_data)
        self.assertIn('ai_explanation', rec)
        self.assertIn('ai_mitigation', rec)
        self.assertIn('ai_controls', rec)
        self.assertIn('NIST', rec['ai_controls'])

    def test_05_pdf_report_generation(self):
        """Test PDF report generation API."""
        res = self.client.post('/api/auth/login', data=json.dumps({'email': 'admin@airiskmanager.com', 'password': 'admin123'}), content_type='application/json')
        token = json.loads(res.data)['token']

        res = self.client.get('/api/reports/pdf?organization=TestCorp', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')
        self.assertGreater(len(res.data), 1000)

if __name__ == '__main__':
    unittest.main()
