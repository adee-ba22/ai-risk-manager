/**
 * AI Risk Manager - PDF Export Helper
 */

async function downloadBackendPDFReport(orgName, assessorName) {
    showToast("Generating executive PDF risk report...", "info");
    try {
        const token = localStorage.getItem('token');
        const url = `/api/reports/pdf?organization=${encodeURIComponent(orgName)}&assessor=${encodeURIComponent(assessorName)}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to generate PDF on server');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `AI_Risk_Assessment_Report_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        showToast("PDF report downloaded successfully!", "success");
    } catch (err) {
        console.error("PDF generation error:", err);
        showToast("Failed to generate PDF: " + err.message, "error");
    }
}
