# AI Risk Manager - Enterprise Cybersecurity Risk Platform

AI Risk Manager is a modern, full-stack cybersecurity risk-management web application for enterprise businesses. It enables organizations to assess, calculate, prioritize, and mitigate security threats using a standardized 5x5 Likelihood × Impact scoring matrix, AI-driven recommendations (via Google Gemini API with intelligent rule-based fallback), full Risk Register CRUD, interactive analytics charts, role-based access control, and executive PDF report generation.

---

## Key Features

1. **Authentication & Session Security**:
   - Secure Sign Up, Sign In, and Logout flows.
   - Hashed password storage using PBKDF2/SHA-256.
   - Protected dashboard routes and active user session badges.

2. **Admin User Tracking & Audit Logs**:
   - Dedicated Admin Users Dashboard (`/admin-users`) tracking user sign-ins, timestamps, IP addresses, roles, and session status.
   - Strict Role-Based Access Control (RBAC): restricts administrative tracking data from standard users.

3. **Main Cybersecurity Dashboard**:
   - Executive scorecards: Overall Cybersecurity Risk Score, Risk Level (Low / Medium / High / Critical), Total Risks, Critical Threats, Open Risks, and Mitigated Risks.
   - Interactive severity distribution donut chart and status breakdown bar chart powered by Chart.js.
   - Recent risk assessment table with quick detail inspection.

4. **Interactive Risk Assessment Calculator**:
   - Comprehensive form capturing Risk Title, Description, Affected Asset, Threat Type, Likelihood (1-5), Impact (1-5), Existing Controls, and Notes.
   - Real-time `Risk Score = Likelihood × Impact` calculation (Range: 1 - 25) with dynamic 5x5 matrix score map.

5. **AI Risk Recommendation Engine**:
   - Dual-engine architecture:
     - **Google Gemini API**: Connects to Gemini API (`GEMINI_API_KEY`) for deep contextual AI analysis.
     - **Deterministic Heuristic Engine**: Intelligent built-in rule fallback operating completely offline when no API key is present.
   - Outputs: Contextual Risk Explanation, Business Impact, Actionable Step-by-Step Mitigation Plan, Priority Level, and Suggested Security Controls (mapped to NIST CSF 2.0 & ISO 27001).

6. **Risk Register & Management (CRUD)**:
   - Complete CRUD: Create, View, Edit, Delete risks.
   - Dynamic filtering by Severity (All, Critical, High, Medium, Low) and Status (Open, In Progress, Mitigated).
   - Instant search bar filtering by title, asset, and threat vector.
   - Quick inline status toggles.

7. **Executive PDF Report Generator**:
   - Generates styled, audit-ready PDF risk reports (via backend ReportLab engine or client-side print export).
   - Includes organization summary, risk score metrics, detailed risk register, AI recommendations, and signature sign-off lines.

8. **10 Responsive SaaS Views**:
   1. Landing Page (Public Hero & Product Showcase)
   2. Sign Up Page
   3. Sign In Page (With Quick Demo Autofill Buttons)
   4. Main Dashboard
   5. Risk Assessment Form
   6. Risk Register
   7. Risk Details Inspection Modal
   8. Reports Page
   9. Admin Users Dashboard (Admin Only)
   10. Profile / Settings Page (Gemini API Key Manager)

---

## Demo Accounts

The database is pre-seeded with sample enterprise users and risks for testing:

| Role | Email Address | Password | Privileges |
|---|---|---|---|
| **Security Administrator** | `admin@airiskmanager.com` | `admin123` | Full Access (Dashboard, Risks, Admin User Tracking, PDF Reports) |
| **Standard User** | `john@example.com` | `user123` | Risk Assessor (Dashboard, Risk Register, Risk Calculator) |
| **Security Analyst** | `sarah.analyst@example.com` | `user123` | Risk Assessor |

---

## Installation & Setup Guide

### Prerequisites
- **Python 3.10+** (Python 3.14 recommended)
- **pip** package manager

### Step 1: Clone / Navigate to Project Directory
```bash
cd C:\Users\user\.gemini\antigravity\scratch\ai-risk-manager
```

### Step 2: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

*(Installed packages: `flask`, `flask-cors`, `reportlab`, `requests`, `werkzeug`)*

---

## Running the Application

To launch the web application server:

```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Running Automated Tests

To execute the automated test suite verifying auth flows, RBAC, risk score calculation, AI fallback engine, and PDF generation:

```bash
python run_tests.py
```

Expected output:
```
Ran 5 tests in 21s
OK
```

---

## Demo Walkthrough Flow

Follow this sequence to test all major capabilities:
1. **Open Platform**: Navigate to `http://127.0.0.1:5000`.
2. **Sign In**: Click **Sign In** -> Click the **Admin Account** demo button (`admin@airiskmanager.com` / `admin123`) -> Click **Sign In**.
3. **View Dashboard**: Observe your name/role badge in top bar, overall risk score, stat cards, and interactive severity/status charts.
4. **Create New Risk**: Navigate to **Risk Assessment** -> Enter title (e.g. *Unencrypted Cloud Storage Bucket*), Likelihood: 4, Impact: 5 -> Observe auto-calculated score `20 (CRITICAL)` -> Click **Preview AI Recommendations** -> Click **Save Risk Assessment**.
5. **Inspect Risk Register**: Navigate to **Risk Register** -> Search for your created risk -> Click the eye icon to view the deep-dive modal -> Change status to **Mitigated**.
6. **Check Admin Users Dashboard**: Click **Admin Users** in sidebar -> View table tracking signed-in users, timestamps, email addresses, and active session status.
7. **Generate Report**: Navigate to **Risk Reports** -> Enter Organization name -> Click **Download PDF Report**.

---

## Project Structure

```
ai-risk-manager/
├── app.py                     # Main Flask application entrypoint & REST API
├── database.py                # SQLite connection manager, schema setup, & CRUD helpers
├── auth.py                    # Password hashing, session token management, & RBAC decorators
├── ai_engine.py               # Gemini AI API caller + Heuristic Rule-Based Fallback Engine
├── report_generator.py        # ReportLab executive PDF report generator
├── schema.sql                 # SQL table definitions for users, sessions, risks, settings
├── seed.py                    # Seeding script for sample users and initial enterprise risks
├── run_tests.py               # Test runner execution script
├── test_app.py                # Automated unit test suite
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables configuration guide
├── static/
│   ├── css/
│   │   └── style.css          # Custom cybersecurity SaaS styles & animations
│   └── js/
│       ├── app.js             # SPA router, view rendering (10 views), toast notifications
│       ├── charts.js          # Chart.js severity & status distribution charts
│       └── pdf.js             # Client-side PDF download handler
└── templates/
    └── index.html             # HTML5 single page app shell with Tailwind CSS & Lucide icons
```

---

## License

Copyright © 2026 AI Risk Manager Enterprise. All rights reserved.
