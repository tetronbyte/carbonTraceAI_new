"""Alert system for ERP extraction failures."""
import os
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime


class AlertSystem:
    """Send alerts for ERP extraction failures."""
    
    def __init__(self):
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_email = os.getenv("ALERT_EMAIL")
        
        # Slack configuration
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    async def send_email_alert(
        self,
        subject: str,
        body: str,
        to_email: Optional[str] = None
    ) -> bool:
        """Send email alert."""
        if not self.smtp_user or not self.smtp_password:
            return False
        
        try:
            recipient = to_email or self.alert_email
            if not recipient:
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = recipient
            msg['Subject'] = f"[CarbonTraceAI] {subject}"
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Failed to send email alert: {str(e)}")
            return False
    
    async def send_slack_alert(
        self,
        title: str,
        message: str,
        color: str = "danger"
    ) -> bool:
        """Send Slack webhook alert."""
        if not self.slack_webhook_url:
            return False
        
        try:
            payload = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": "CarbonTraceAI ERP Integration",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.slack_webhook_url, json=payload)
                return response.status_code == 200
        
        except Exception as e:
            print(f"Failed to send Slack alert: {str(e)}")
            return False
    
    async def alert_consecutive_failures(
        self,
        tenant_id: str,
        erp_type: str,
        failure_count: int
    ):
        """Alert on consecutive failures."""
        subject = f"ERP Extraction Failures: {erp_type}"
        
        email_body = f"""
        <html>
        <body>
            <h2>⚠️ ERP Extraction Alert</h2>
            <p><strong>Tenant ID:</strong> {tenant_id}</p>
            <p><strong>ERP Type:</strong> {erp_type}</p>
            <p><strong>Consecutive Failures:</strong> {failure_count}</p>
            <p><strong>Time:</strong> {datetime.now().isoformat()}</p>
            
            <h3>Action Required</h3>
            <ul>
                <li>Check ERP credentials</li>
                <li>Verify network connectivity</li>
                <li>Review audit logs in dashboard</li>
            </ul>
            
            <p>
                <a href="https://your-domain.com/erp/connections">View ERP Connections</a>
            </p>
        </body>
        </html>
        """
        
        slack_message = f"""
*Tenant:* `{tenant_id}`
*ERP:* `{erp_type}`
*Failures:* {failure_count} consecutive
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

*Action:* Check credentials and connectivity
        """
        
        # Send both email and Slack alerts
        await self.send_email_alert(subject, email_body)
        await self.send_slack_alert(
            title=f"🚨 {failure_count}x ERP Failures: {erp_type}",
            message=slack_message,
            color="danger"
        )
    
    async def alert_validation_threshold(
        self,
        tenant_id: str,
        erp_type: str,
        failure_count: int,
        threshold: int = 50
    ):
        """Alert when validation failures exceed threshold."""
        if failure_count < threshold:
            return
        
        subject = f"High Validation Failures: {erp_type}"
        
        email_body = f"""
        <html>
        <body>
            <h2>⚠️ Validation Failures Alert</h2>
            <p><strong>Tenant ID:</strong> {tenant_id}</p>
            <p><strong>ERP Type:</strong> {erp_type}</p>
            <p><strong>Failures:</strong> {failure_count} (threshold: {threshold})</p>
            
            <h3>Possible Causes</h3>
            <ul>
                <li>Data quality issues in ERP</li>
                <li>Missing field mappings</li>
                <li>Incorrect unit conversions</li>
            </ul>
            
            <p>
                <a href="https://your-domain.com/erp/validation-failures/{tenant_id}">
                    View Validation Failures
                </a>
            </p>
        </body>
        </html>
        """
        
        await self.send_email_alert(subject, email_body)
        await self.send_slack_alert(
            title=f"⚠️ High Validation Failures: {erp_type}",
            message=f"Tenant `{tenant_id}` has {failure_count} validation failures",
            color="warning"
        )
    
    async def alert_sync_lag(
        self,
        tenant_id: str,
        erp_type: str,
        module: str,
        lag_hours: float,
        threshold_hours: int = 24
    ):
        """Alert when sync lag exceeds threshold."""
        if lag_hours < threshold_hours:
            return
        
        subject = f"ERP Sync Lag: {erp_type}"
        
        slack_message = f"""
*Tenant:* `{tenant_id}`
*ERP:* `{erp_type}`
*Module:* `{module}`
*Lag:* {lag_hours:.1f} hours (threshold: {threshold_hours}h)

*Action:* Trigger manual sync or check extraction issues
        """
        
        await self.send_slack_alert(
            title=f"⏰ ERP Sync Lag: {erp_type}",
            message=slack_message,
            color="warning"
        )
    
    async def alert_extraction_success(
        self,
        tenant_id: str,
        erp_type: str,
        records_count: int
    ):
        """Send success notification (optional)."""
        slack_message = f"""
✅ *ERP Extraction Complete*
*Tenant:* `{tenant_id}`
*ERP:* `{erp_type}`
*Records:* {records_count}
        """
        
        await self.send_slack_alert(
            title="✅ Extraction Success",
            message=slack_message,
            color="good"
        )


# Global alert system instance
alert_system = AlertSystem()
