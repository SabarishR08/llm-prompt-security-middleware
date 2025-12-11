"""Alerts service for email/SMS notifications.

Supports SMTP email, SendGrid API, and Twilio SMS. Designed to fail-safe
(with logging) when credentials are missing.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Dict, Any, Optional
import requests


class AlertsService:
    """Send alerts for high-severity events (PII, injections, blocked prompts)."""

    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings or {}
        # Alert levels can be: off < low < medium < high
        self.alert_level = (self.settings.get("alert_level") or "medium").lower()
        self.smtp_cfg = self.settings.get("smtp", {})
        self.sendgrid_cfg = self.settings.get("sendgrid", {})
        self.twilio_cfg = self.settings.get("twilio", {})

    def _level_allows(self, severity: str) -> bool:
        order = {"off": 0, "low": 1, "medium": 2, "high": 3}
        return order.get(severity, 1) <= order.get(self.alert_level, 2)

    # -----------------
    # SMTP Email
    # -----------------
    def send_email_smtp(self, subject: str, body: str, to_addr: str) -> bool:
        if not self.smtp_cfg:
            return False
        host = self.smtp_cfg.get("host")
        port = self.smtp_cfg.get("port", 587)
        username = self.smtp_cfg.get("username")
        password = self.smtp_cfg.get("password")
        sender = self.smtp_cfg.get("from", username)
        if not all([host, username, password, sender]):
            return False
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_addr
            msg.set_content(body)
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(username, password)
                smtp.send_message(msg)
            return True
        except Exception:
            return False

    # -----------------
    # SendGrid Email API
    # -----------------
    def send_email_sendgrid(self, subject: str, body: str, to_addr: str) -> bool:
        api_key = self.sendgrid_cfg.get("api_key")
        sender = self.sendgrid_cfg.get("from")
        if not api_key or not sender:
            return False
        try:
            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "personalizations": [{"to": [{"email": to_addr}]}],
                    "from": {"email": sender},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
                timeout=8,
            )
            return resp.status_code in (200, 202)
        except Exception:
            return False

    # -----------------
    # Twilio SMS API
    # -----------------
    def send_sms_twilio(self, body: str, to_number: str) -> bool:
        account = self.twilio_cfg.get("account_sid")
        token = self.twilio_cfg.get("auth_token")
        from_num = self.twilio_cfg.get("from_number")
        if not all([account, token, from_num, to_number]):
            return False
        try:
            resp = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account}/Messages.json",
                auth=(account, token),
                data={"From": from_num, "To": to_number, "Body": body},
                timeout=8,
            )
            return resp.status_code in (200, 201)
        except Exception:
            return False

    # -----------------
    # Unified trigger
    # -----------------
    def trigger_alert(self, event: str, severity: str, details: Dict[str, Any]):
        """Trigger alerts when severity meets configured level.

        event: e.g., "blocked", "pii_high", "injection", "toxicity".
        severity: low|medium|high
        details: context payload (prompt, reasons, user, etc.)
        """
        if not self._level_allows(severity):
            return False

        subject = f"[AI Compliance] {event.title()} detected"
        body_lines = [f"Event: {event}", f"Severity: {severity}"]
        for k, v in (details or {}).items():
            body_lines.append(f"{k}: {v}")
        body = "\n".join(body_lines)

        # Email (SMTP or SendGrid)
        to_email = self.settings.get("alert_email")
        email_sent = False
        if to_email:
            email_sent = self.send_email_sendgrid(subject, body, to_email) or self.send_email_smtp(subject, body, to_email)

        # SMS (Twilio)
        to_sms = self.settings.get("alert_sms")
        sms_sent = False
        if to_sms:
            sms_sent = self.send_sms_twilio(body, to_sms)

        return email_sent or sms_sent
