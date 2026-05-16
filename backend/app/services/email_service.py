"""Email Service for the Skill2Job Placement System.

Provides email notification capabilities for:
- Password reset links
- Placement updates (shortlisted, selected, rejected)
- New job opening alerts
- Profile completion reminders
- Application status changes

Supports SMTP (Gmail, Outlook, custom) and falls back to logging
when email is not configured (development mode).
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from flask import current_app

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails via SMTP."""

    def __init__(self):
        self.smtp_host = os.environ.get('SMTP_HOST', '')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@skill2job.com')
        self.from_name = os.environ.get('FROM_NAME', 'Skill2Job')
        self.is_configured = bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None,
    ) -> bool:
        """Send an email to a recipient.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_body: HTML content of the email.
            plain_body: Optional plain text fallback.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.is_configured:
            logger.info(
                "[EMAIL-DEV] To: %s | Subject: %s | Body: %s",
                to_email, subject, plain_body or html_body[:200]
            )
            return True  # Succeed silently in dev mode

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            if plain_body:
                msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info("Email sent to %s: %s", to_email, subject)
            return True

        except Exception as e:
            logger.exception("Failed to send email to %s: %s", to_email, e)
            return False

    # ------------------------------------------------------------------
    # Notification Templates
    # ------------------------------------------------------------------

    def send_password_reset(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email with token link."""
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"

        subject = "Skill2Job - Password Reset Request"
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Skill2Job</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1e293b; margin-top: 0;">Password Reset</h2>
                <p style="color: #64748b;">Hi {user_name},</p>
                <p style="color: #64748b;">We received a request to reset your password. Click the button below to set a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: #4f46e5; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: 600;">Reset Password</a>
                </div>
                <p style="color: #94a3b8; font-size: 14px;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
            </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\nReset your password: {reset_link}\n\nThis link expires in 1 hour."

        return self.send_email(to_email, subject, html_body, plain_body)

    def send_shortlist_notification(
        self, to_email: str, user_name: str, job_title: str, company_name: str
    ) -> bool:
        """Notify student they've been shortlisted for a role."""
        subject = f"Skill2Job - You've been shortlisted for {job_title}!"
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Skill2Job</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1e293b; margin-top: 0;">🎉 Congratulations!</h2>
                <p style="color: #64748b;">Hi {user_name},</p>
                <p style="color: #64748b;">Great news! You've been <strong>shortlisted</strong> for the following position:</p>
                <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: 600; color: #1e293b; font-size: 18px;">{job_title}</p>
                    <p style="margin: 5px 0 0; color: #64748b;">{company_name}</p>
                </div>
                <p style="color: #64748b;">Please check your dashboard for next steps and prepare for the upcoming rounds.</p>
                <p style="color: #64748b;">Best of luck!</p>
            </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\nYou've been shortlisted for {job_title} at {company_name}.\n\nCheck your dashboard for next steps."

        return self.send_email(to_email, subject, html_body, plain_body)

    def send_new_job_alert(
        self, to_email: str, user_name: str, job_title: str, company_name: str, compatibility_score: float
    ) -> bool:
        """Alert student about a new job matching their profile."""
        subject = f"Skill2Job - New job match: {job_title} ({compatibility_score:.0f}% match)"
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Skill2Job</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1e293b; margin-top: 0;">📋 New Job Match</h2>
                <p style="color: #64748b;">Hi {user_name},</p>
                <p style="color: #64748b;">A new job opening matches your skill profile:</p>
                <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: 600; color: #1e293b; font-size: 18px;">{job_title}</p>
                    <p style="margin: 5px 0 0; color: #64748b;">{company_name}</p>
                    <p style="margin: 10px 0 0; color: #4f46e5; font-weight: 600; font-size: 16px;">{compatibility_score:.0f}% Compatibility</p>
                </div>
                <p style="color: #64748b;">Log in to view details and check your skill gap for this role.</p>
            </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\nNew job match: {job_title} at {company_name} ({compatibility_score:.0f}% match).\n\nLog in to view details."

        return self.send_email(to_email, subject, html_body, plain_body)

    def send_placement_confirmation(
        self, to_email: str, user_name: str, job_title: str, company_name: str
    ) -> bool:
        """Notify student of confirmed placement."""
        subject = f"Skill2Job - Placement Confirmed at {company_name}!"
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Skill2Job</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1e293b; margin-top: 0;">🎊 Placement Confirmed!</h2>
                <p style="color: #64748b;">Hi {user_name},</p>
                <p style="color: #64748b;">We're thrilled to inform you that your placement has been <strong>confirmed</strong>!</p>
                <div style="background: #d1fae5; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #a7f3d0;">
                    <p style="margin: 0; font-weight: 600; color: #065f46; font-size: 18px;">{job_title}</p>
                    <p style="margin: 5px 0 0; color: #047857;">{company_name}</p>
                </div>
                <p style="color: #64748b;">Congratulations on this achievement! Your hard work has paid off.</p>
            </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\nYour placement is confirmed!\n\nRole: {job_title}\nCompany: {company_name}\n\nCongratulations!"

        return self.send_email(to_email, subject, html_body, plain_body)

    def send_profile_reminder(self, to_email: str, user_name: str, completeness: int) -> bool:
        """Remind student to complete their profile."""
        subject = "Skill2Job - Complete your profile to get better job matches"
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Skill2Job</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1e293b; margin-top: 0;">📝 Complete Your Profile</h2>
                <p style="color: #64748b;">Hi {user_name},</p>
                <p style="color: #64748b;">Your profile is currently <strong>{completeness}% complete</strong>. A complete profile helps our AI match you with better job opportunities.</p>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <div style="background: #e2e8f0; border-radius: 4px; height: 12px; overflow: hidden;">
                        <div style="background: #4f46e5; height: 100%; width: {completeness}%; border-radius: 4px;"></div>
                    </div>
                    <p style="margin: 8px 0 0; color: #64748b; font-size: 14px; text-align: center;">{completeness}% Complete</p>
                </div>
                <p style="color: #64748b;">Add your skills, projects, and certifications to improve your matches.</p>
            </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\nYour profile is {completeness}% complete. Add skills, projects, and certifications to get better job matches."

        return self.send_email(to_email, subject, html_body, plain_body)

    def send_application_status_update(
        self, to_email: str, user_name: str, job_title: str, company_name: str, new_status: str
    ) -> bool:
        """Notify student of application status change."""
        status_colors = {
            "shortlisted": "#4f46e5",
            "interviewed": "#f59e0b",
            "selected": "#10b981",
            "rejected": "#ef4444",
        }
        color = status_colors.get(new_status, "#64748b")

        subject = f"Skill2Job - Application Update: {job_title}"
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Skill2Job</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
                <h2 style="color: #1e293b; margin-top: 0;">Application Status Update</h2>
                <p style="color: #64748b;">Hi {user_name},</p>
                <p style="color: #64748b;">Your application status has been updated:</p>
                <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: 600; color: #1e293b;">{job_title}</p>
                    <p style="margin: 5px 0 0; color: #64748b;">{company_name}</p>
                    <p style="margin: 10px 0 0;">
                        <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 14px; font-weight: 600; text-transform: uppercase;">{new_status}</span>
                    </p>
                </div>
                <p style="color: #64748b;">Log in to your dashboard for more details.</p>
            </div>
        </div>
        """
        plain_body = f"Hi {user_name},\n\nYour application for {job_title} at {company_name} has been updated to: {new_status}."

        return self.send_email(to_email, subject, html_body, plain_body)


# Module-level singleton
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
