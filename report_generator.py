import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import database as db

def generate_pdf_report(organization_name="Enterprise Security Operations", assessor_name="Security Administrator"):
    """
    Generate an executive PDF risk assessment report.
    Returns bytes buffer of the PDF file.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_LEFT
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    badge_critical = ParagraphStyle('BadgeCrit', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#ef4444'))
    badge_high = ParagraphStyle('BadgeHigh', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#f97316'))
    badge_med = ParagraphStyle('BadgeMed', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#eab308'))
    badge_low = ParagraphStyle('BadgeLow', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#10b981'))

    story = []

    # Header section
    now_str = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
    story.append(Paragraph("AI RISK MANAGER", ParagraphStyle('TopNav', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#6366f1'))))
    story.append(Paragraph("Executive Cybersecurity Risk Assessment Report", title_style))
    story.append(Paragraph(f"<b>Organization:</b> {organization_name} &nbsp;|&nbsp; <b>Assessor:</b> {assessor_name} &nbsp;|&nbsp; <b>Generated:</b> {now_str}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=5, spaceAfter=15))

    # Metrics Summary Box
    metrics = db.get_dashboard_metrics()

    metric_data = [
        [
            Paragraph(f"<b>Overall Risk Score</b><br/><font size=16 color='#1e293b'><b>{metrics['avg_risk_score']} / 25</b></font>", body_style),
            Paragraph(f"<b>Overall Risk Level</b><br/><font size=16 color='#ef4444'><b>{metrics['overall_risk_level']}</b></font>", body_style),
            Paragraph(f"<b>Total Risks</b><br/><font size=16 color='#3b82f6'><b>{metrics['total_risks']}</b></font>", body_style),
            Paragraph(f"<b>Critical Risks</b><br/><font size=16 color='#ef4444'><b>{metrics['critical_risks']}</b></font>", body_style),
            Paragraph(f"<b>Mitigated Risks</b><br/><font size=16 color='#10b981'><b>{metrics['mitigated_risks']}</b></font>", body_style),
        ]
    ]

    metric_table = Table(metric_data, colWidths=[108, 108, 108, 108, 108])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 15))

    # Executive Overview text
    story.append(Paragraph("Executive Summary", h2_style))
    overview_text = (
        f"This report presents an automated risk evaluation conducted by the AI Risk Manager platform. "
        f"A total of <b>{metrics['total_risks']} cybersecurity risks</b> were assessed across enterprise infrastructure and assets. "
        f"Currently, <b>{metrics['critical_risks']} critical</b> and <b>{metrics['high_risks']} high-severity</b> risks require immediate remediation action. "
        f"<b>{metrics['mitigated_risks']} risks</b> have been successfully mitigated."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 15))

    # Detailed Risk Register Table
    story.append(Paragraph("Identified Risks & AI Recommendations", h2_style))

    all_risks = db.get_all_risks()

    if not all_risks:
        story.append(Paragraph("<i>No cybersecurity risks currently recorded in the risk register.</i>", body_style))
    else:
        table_headers = [
            Paragraph("Risk Name & Asset", table_header_style),
            Paragraph("Threat Type", table_header_style),
            Paragraph("L × I", table_header_style),
            Paragraph("Score", table_header_style),
            Paragraph("Severity", table_header_style),
            Paragraph("Status", table_header_style),
            Paragraph("AI Recommended Action", table_header_style),
        ]

        table_rows = [table_headers]

        for r in all_risks:
            sev = r['severity']
            if sev == 'Critical':
                badge_style = badge_critical
            elif sev == 'High':
                badge_style = badge_high
            elif sev == 'Medium':
                badge_style = badge_med
            else:
                badge_style = badge_low

            ai_mit = r.get('ai_mitigation', 'N/A')
            if len(ai_mit) > 120:
                ai_mit = ai_mit[:117] + "..."

            row = [
                Paragraph(f"<b>{r['title']}</b><br/><font color='#64748b'>Asset: {r['asset']}</font>", body_style),
                Paragraph(r['threat_type'], body_style),
                Paragraph(f"{r['likelihood']} × {r['impact']}", body_style),
                Paragraph(f"<b>{r['risk_score']}</b>", body_style),
                Paragraph(f"<b>{r['severity']}</b>", badge_style),
                Paragraph(f"<b>{r['status']}</b>", body_style),
                Paragraph(ai_mit.replace('\n', '<br/>'), body_style),
            ]
            table_rows.append(row)

        risk_table = Table(table_rows, colWidths=[100, 75, 35, 35, 50, 55, 190])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        story.append(risk_table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Report Sign-off & Compliance Verification</b>", h2_style))
    story.append(Paragraph("This risk assessment report was compiled and verified using AI Risk Manager SaaS.", body_style))
    story.append(Spacer(1, 25))

    # Signature line
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Chief Information Security Officer</b>", body_style),
            Paragraph("____________________________<br/><b>Lead Risk Assessor</b>", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
