"""Email Notification Service for IT Support System"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
        self.smtp_from = config.SMTP_FROM
        self.enabled = config.SMTP_ENABLED
        
        if not self.enabled:
            logger.warning("Email service is disabled. Set SMTP_USER and SMTP_PASSWORD in environment to enable.")
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send an email"""
        if not self.enabled:
            logger.info(f"Email service disabled. Would have sent to {to_email}: {subject}")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            
            # Add plain text version
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_ticket_created(self, user_email: str, user_name: str, ticket_id: str, 
                            category: str, subject: str, description: str, priority: str):
        """Send notification when a ticket is created"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .ticket-id {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .label {{ font-weight: bold; color: #555; }}
                .priority {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
                .priority-low {{ background: #e3f2fd; color: #1976d2; }}
                .priority-medium {{ background: #fff3e0; color: #f57c00; }}
                .priority-high {{ background: #ffebee; color: #d32f2f; }}
                .priority-critical {{ background: #d32f2f; color: white; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎫 Ticket Created</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Your support ticket has been successfully created. Our team will review it shortly.</p>
                    
                    <div class="ticket-info">
                        <div class="ticket-id">{ticket_id}</div>
                        <p><span class="label">Category:</span> {category}</p>
                        <p><span class="label">Subject:</span> {subject}</p>
                        <p><span class="label">Priority:</span> <span class="priority priority-{priority.lower()}">{priority}</span></p>
                        <p><span class="label">Description:</span></p>
                        <p style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{description[:500]}{'...' if len(description) > 500 else ''}</p>
                    </div>
                    
                    <p>You can track the status of your ticket by logging into the IT Support Portal.</p>
                    <p>Thank you for your patience!</p>
                </div>
                <div class="footer">
                    <p>IT Support System - Powered by AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hi {user_name},
        
        Your support ticket has been created successfully.
        
        Ticket ID: {ticket_id}
        Category: {category}
        Subject: {subject}
        Priority: {priority}
        
        Description:
        {description[:500]}{'...' if len(description) > 500 else ''}
        
        Our team will review your ticket and get back to you soon.
        
        Thank you,
        IT Support Team
        """
        
        return self._send_email(
            user_email,
            f"[{ticket_id}] Ticket Created: {subject}",
            html_body,
            text_body
        )
    
    def send_ticket_status_updated(self, user_email: str, user_name: str, ticket_id: str,
                                   subject: str, old_status: str, new_status: str, 
                                   resolution_notes: str = None):
        """Send notification when ticket status is updated"""
        status_colors = {
            'Open': '#2196f3',
            'In Progress': '#ff9800',
            'Resolved': '#4caf50',
            'Closed': '#9e9e9e'
        }
        
        resolution_html = ""
        resolution_text = ""
        if resolution_notes and new_status in ['Resolved', 'Closed']:
            resolution_html = f"""
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <p><span class="label">Resolution Notes:</span></p>
                <p>{resolution_notes}</p>
            </div>
            """
            resolution_text = f"\n\nResolution Notes:\n{resolution_notes}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .ticket-id {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .label {{ font-weight: bold; color: #555; }}
                .status {{ display: inline-block; padding: 6px 16px; border-radius: 16px; font-weight: bold; color: white; }}
                .status-change {{ display: flex; align-items: center; gap: 10px; margin: 15px 0; }}
                .arrow {{ font-size: 20px; color: #666; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔄 Ticket Status Updated</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>The status of your support ticket has been updated.</p>
                    
                    <div class="ticket-info">
                        <div class="ticket-id">{ticket_id}</div>
                        <p><span class="label">Subject:</span> {subject}</p>
                        
                        <div class="status-change">
                            <span class="status" style="background: {status_colors.get(old_status, '#666')}">{old_status}</span>
                            <span class="arrow">➜</span>
                            <span class="status" style="background: {status_colors.get(new_status, '#666')}">{new_status}</span>
                        </div>
                    </div>
                    
                    {resolution_html}
                    
                    <p>You can view full details by logging into the IT Support Portal.</p>
                </div>
                <div class="footer">
                    <p>IT Support System - Powered by AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hi {user_name},
        
        The status of your support ticket has been updated.
        
        Ticket ID: {ticket_id}
        Subject: {subject}
        
        Status changed: {old_status} → {new_status}
        {resolution_text}
        
        Thank you,
        IT Support Team
        """
        
        return self._send_email(
            user_email,
            f"[{ticket_id}] Status Updated: {old_status} → {new_status}",
            html_body,
            text_body
        )
    
    def send_ticket_assigned(self, user_email: str, user_name: str, ticket_id: str,
                            subject: str, technician_name: str, technician_email: str):
        """Send notification when ticket is assigned to a technician"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .ticket-id {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .label {{ font-weight: bold; color: #555; }}
                .technician-card {{ background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; }}
                .tech-name {{ font-size: 18px; font-weight: bold; color: #2e7d32; }}
                .tech-email {{ color: #558b2f; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👨‍💻 Technician Assigned</h1>
                </div>
                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Great news! A technician has been assigned to your support ticket and will begin working on it shortly.</p>
                    
                    <div class="ticket-info">
                        <div class="ticket-id">{ticket_id}</div>
                        <p><span class="label">Subject:</span> {subject}</p>
                    </div>
                    
                    <div class="technician-card">
                        <p style="margin: 0; color: #666;">Assigned Technician</p>
                        <p class="tech-name">👤 {technician_name}</p>
                        <p class="tech-email">📧 {technician_email}</p>
                    </div>
                    
                    <p>You will receive updates as your ticket progresses.</p>
                </div>
                <div class="footer">
                    <p>IT Support System - Powered by AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hi {user_name},
        
        A technician has been assigned to your support ticket.
        
        Ticket ID: {ticket_id}
        Subject: {subject}
        
        Assigned Technician: {technician_name}
        Email: {technician_email}
        
        You will receive updates as your ticket progresses.
        
        Thank you,
        IT Support Team
        """
        
        return self._send_email(
            user_email,
            f"[{ticket_id}] Technician Assigned: {technician_name}",
            html_body,
            text_body
        )
    
    def send_technician_assignment(self, tech_email: str, tech_name: str, ticket_id: str,
                                   user_name: str, category: str, subject: str, 
                                   description: str, priority: str):
        """Send notification to technician when assigned a ticket"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .ticket-id {{ font-size: 24px; font-weight: bold; color: #ee5a6f; }}
                .label {{ font-weight: bold; color: #555; }}
                .priority {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
                .priority-low {{ background: #e3f2fd; color: #1976d2; }}
                .priority-medium {{ background: #fff3e0; color: #f57c00; }}
                .priority-high {{ background: #ffebee; color: #d32f2f; }}
                .priority-critical {{ background: #d32f2f; color: white; }}
                .user-info {{ background: #e3f2fd; padding: 10px; border-radius: 8px; margin: 10px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎫 New Ticket Assigned to You</h1>
                </div>
                <div class="content">
                    <p>Hi {tech_name},</p>
                    <p>A new support ticket has been assigned to you. Please review and take action.</p>
                    
                    <div class="ticket-info">
                        <div class="ticket-id">{ticket_id}</div>
                        <p><span class="label">Category:</span> {category}</p>
                        <p><span class="label">Subject:</span> {subject}</p>
                        <p><span class="label">Priority:</span> <span class="priority priority-{priority.lower()}">{priority}</span></p>
                        
                        <div class="user-info">
                            <span class="label">Submitted by:</span> {user_name}
                        </div>
                        
                        <p><span class="label">Description:</span></p>
                        <p style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{description[:500]}{'...' if len(description) > 500 else ''}</p>
                    </div>
                    
                    <p>Please log into the Admin Dashboard to manage this ticket.</p>
                </div>
                <div class="footer">
                    <p>IT Support System - Powered by AI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hi {tech_name},
        
        A new support ticket has been assigned to you.
        
        Ticket ID: {ticket_id}
        Category: {category}
        Subject: {subject}
        Priority: {priority}
        Submitted by: {user_name}
        
        Description:
        {description[:500]}{'...' if len(description) > 500 else ''}
        
        Please log into the Admin Dashboard to manage this ticket.
        
        IT Support Team
        """
        
        return self._send_email(
            tech_email,
            f"[ASSIGNED] {ticket_id}: {subject} ({priority})",
            html_body,
            text_body
        )


# Singleton instance
email_service = EmailService()
