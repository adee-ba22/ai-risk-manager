import os
import json
import requests
import database as db

def generate_ai_recommendation(risk_data, api_key=None):
    """
    Generate AI risk analysis & recommendations.
    Uses Google Gemini API if key is available, else falls back to intelligent rule-based engine.
    """
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY') or db.get_setting('gemini_api_key')

    if api_key:
        try:
            return generate_gemini_recommendation(risk_data, api_key)
        except Exception as e:
            print(f"[AI Engine Warning] Gemini API call failed: {e}. Falling back to Rule-Based Engine.")
            return generate_rule_based_recommendation(risk_data)
    else:
        return generate_rule_based_recommendation(risk_data)

def generate_gemini_recommendation(risk_data, api_key):
    """Query Gemini 1.5/2.0 API for cybersecurity risk analysis."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""
You are a Lead Cybersecurity Risk Analyst & CISO. Analyze the following business risk scenario and provide detailed risk analysis and mitigation recommendations.

Risk Details:
- Title: {risk_data.get('title')}
- Description: {risk_data.get('description')}
- Asset Affected: {risk_data.get('asset')}
- Threat Type: {risk_data.get('threat_type')}
- Likelihood (1-5): {risk_data.get('likelihood')}
- Impact (1-5): {risk_data.get('impact')}
- Existing Controls: {risk_data.get('existing_controls', 'None reported')}
- Notes: {risk_data.get('notes', 'N/A')}

Return a valid JSON object with EXACTLY these keys:
{{
  "ai_explanation": "Detailed explanation of the risk mechanism and technical vector.",
  "why_important": "Business impact explanation detailing potential operational, financial, legal, or reputational damage.",
  "ai_mitigation": "Numbered step-by-step actionable mitigation plan.",
  "ai_priority": "Immediate / High / Medium / Low",
  "ai_controls": "Suggested Security Controls mapped to NIST CSF 2.0 and ISO 27001 standards."
}}
Do NOT include markdown formatting or extra text outside the JSON object.
"""

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=12)
    if response.status_code == 200:
        res_data = response.json()
        text_content = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        # Clean JSON codeblock wrappers if present
        if text_content.startswith('```'):
            text_content = text_content.split('```')[1]
            if text_content.startswith('json'):
                text_content = text_content[4:]
            text_content = text_content.strip()
        return json.loads(text_content)
    else:
        raise Exception(f"Gemini API returned status {response.status_code}: {response.text}")

def generate_rule_based_recommendation(risk_data):
    """Intelligent fallback heuristic engine for risk assessment."""
    threat = str(risk_data.get('threat_type', '')).lower()
    asset = str(risk_data.get('asset', '')).lower()
    title = str(risk_data.get('title', '')).lower()
    likelihood = int(risk_data.get('likelihood', 3))
    impact = int(risk_data.get('impact', 3))
    score = likelihood * impact

    # Determine priority
    if score >= 16:
        priority = "Immediate Action Required"
    elif score >= 10:
        priority = "High Priority"
    elif score >= 5:
        priority = "Medium Priority"
    else:
        priority = "Low Priority"

    # Match threat rules
    if "ransomware" in threat or "malware" in threat or "ransomware" in title:
        explanation = f"The identified threat introduces severe risk of malicious data encryption and operational paralysis targeting {risk_data.get('asset')}. Attackers exploit unpatched vulnerabilities or compromised credentials to execute lateral movement and exfiltrate sensitive files."
        why_important = "Ransomware infections result in complete business outage, extortion demands, loss of customer trust, regulatory fines, and permanent data loss if immutable backups are unavailable."
        mitigation = (
            "1. Enforce automated Endpoint Detection and Response (EDR) agents on all hosts.\n"
            "2. Implement 3-2-1-1-0 immutable offsite backup policy isolated from active Directory.\n"
            "3. Enforce strict network micro-segmentation to limit lateral movement.\n"
            "4. Accelerate critical OS and application patch deployment within 48 hours."
        )
        controls = "NIST CSF: PR.DS-1, PR.IP-4, DE.CM-1 | ISO 27001: A.12.2.1, A.12.6.1"

    elif "data breach" in threat or "leak" in threat or "leakage" in threat or "database" in asset:
        explanation = f"Unauthorized access or exposure of confidential business data stored in {risk_data.get('asset')}. Risk stems from missing encryption, permissive bucket permissions, or compromised database credentials."
        why_important = "Data exposure leads to massive GDPR/CCPA regulatory penalties, class-action lawsuits, intellectual property loss, and catastrophic reputational damage."
        mitigation = (
            "1. Enforce AES-256 encryption at rest and TLS 1.3 in transit across all storage resources.\n"
            "2. Implement strict Role-Based Access Control (RBAC) with Least Privilege access policies.\n"
            "3. Deploy Data Loss Prevention (DLP) tools to monitor outbound payload transfers.\n"
            "4. Enable database query audit logging with real-time SIEM alerts."
        )
        controls = "NIST CSF: PR.DS-5, PR.AC-4, DE.AE-2 | ISO 27001: A.10.1.1, A.13.2.1"

    elif "phishing" in threat or "social engineering" in threat or "email" in asset:
        explanation = f"Threat actors leverage targeted spear-phishing or credential harvesting campaigns to trick employees accessing {risk_data.get('asset')}, leading to account takeover."
        why_important = "Human error accounts for over 80% of enterprise security breaches. Initial access gained via phishing serves as a launchpad for BEC (Business Email Compromise) and network intrusion."
        mitigation = (
            "1. Mandate FIDO2/WebAuthn hardware security keys for MFA across all enterprise accounts.\n"
            "2. Deploy Secure Email Gateway (SEG) with automated URL sandboxing and spoof prevention.\n"
            "3. Conduct monthly automated phishing simulations and security awareness training.\n"
            "4. Configure DMARC (p=reject), DKIM, and SPF records."
        )
        controls = "NIST CSF: PR.AT-1, PR.AC-1, DE.CM-7 | ISO 27001: A.7.2.2, A.9.4.2"

    elif "unauthorized access" in threat or "identity" in threat or "privilege" in threat:
        explanation = f"Weak identity security or excessive privileges allow unauthorized entities to access critical systems on {risk_data.get('asset')}."
        why_important = "Privilege escalation allows threat actors to gain domain administrative rights, tamper with audit logs, and quietly persistent access."
        mitigation = (
            "1. Implement Privileged Access Management (PAM) with just-in-time credential elevation.\n"
            "2. Enforce Mandatory Multi-Factor Authentication (MFA) on all external gateways.\n"
            "3. Perform quarterly access reviews to prune dormant user accounts and redundant permissions.\n"
            "4. Enable continuous session monitoring and automated session termination."
        )
        controls = "NIST CSF: PR.AC-6, PR.AC-7, DE.CM-3 | ISO 27001: A.9.2.6, A.9.4.1"

    elif "misconfiguration" in threat or "cloud" in threat or "s3" in asset:
        explanation = f"Improper security parameters, default passwords, or public access misconfigurations on {risk_data.get('asset')} leave resources exposed to internet scanners."
        why_important = "Automated threat scanners identify public cloud storage and open admin ports within minutes, resulting in immediate unauthorized exposure."
        mitigation = (
            "1. Deploy Cloud Security Posture Management (CSPM) to automatically detect configuration drift.\n"
            "2. Enforce Infrastructure as Code (IaC) static security scanning in CI/CD pipelines.\n"
            "3. Lock down public IP access; require Zero-Trust Network Access (ZTNA) or VPN.\n"
            "4. Disable default admin accounts and enforce strong password policies."
        )
        controls = "NIST CSF: PR.IP-1, PR.IP-3, DE.CM-8 | ISO 27001: A.12.6.1, A.14.2.2"

    elif "supply chain" in threat or "third-party" in threat or "vendor" in threat:
        explanation = f"Vulnerabilities in third-party libraries, open-source packages, or vendor services linked to {risk_data.get('asset')} compromise enterprise integrity."
        why_important = "Supply chain attacks bypass perimeter defenses by exploiting trusted third-party access paths and software updates."
        mitigation = (
            "1. Generate and continuously audit Software Bill of Materials (SBOM) for all software.\n"
            "2. Require third-party vendors to submit SOC 2 Type II reports and ISO 27001 certificates.\n"
            "3. Isolate vendor integrations within dedicated API gateways and sandbox environments.\n"
            "4. Implement automated Dependency Track scanning for zero-day CVE notifications."
        )
        controls = "NIST CSF: ID.SC-1, ID.SC-3, PR.DS-6 | ISO 27001: A.15.1.1, A.15.2.1"

    else:
        # Generic comprehensive cybersecurity baseline rule
        explanation = f"Security exposure affecting {risk_data.get('asset')} due to {risk_data.get('threat_type')}. Current controls require enhancement to mitigate potential exploitation."
        why_important = f"Unmanaged risk score of {score} represents significant exposure to operational disruption, data leakage, and compliance non-conformity."
        mitigation = (
            "1. Conduct comprehensive vulnerability scanning and penetration testing on target asset.\n"
            "2. Restrict network access policies and enforce strict Zero Trust Network Architecture.\n"
            "3. Verify logging coverage and ensure events forward to central SIEM for 24/7 detection.\n"
            "4. Establish formally documented Incident Response Playbook for this specific threat vector."
        )
        controls = "NIST CSF: ID.RA-3, PR.IP-1, DE.AE-1 | ISO 27001: A.12.1.1, A.12.6.1"

    return {
        "ai_explanation": explanation,
        "why_important": why_important,
        "ai_mitigation": mitigation,
        "ai_priority": priority,
        "ai_controls": controls
    }
