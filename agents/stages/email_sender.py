"""Stage 7: Email Delivery - Send HTML report via email."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import json
from pathlib import Path
import re

from agents.config import config

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends HTML email reports."""

    def __init__(self):
        self.config = config.email

    def send_report(
        self,
        html_content: str,
        subject: Optional[str] = None,
        to_email: Optional[str] = None,
    ) -> bool:
        """
        Send HTML email report.

        Args:
            html_content: HTML content for email body.
            subject: Email subject line (optional, will auto-generate).
            to_email: Recipient email (optional, uses config default).

        Returns:
            True if sent successfully, False otherwise.
        """
        # Validate configuration
        if not all(
            [
                self.config.smtp_username,
                self.config.smtp_password,
                self.config.from_email,
            ]
        ):
            logger.error("Email configuration incomplete. Check SMTP settings.")
            return False

        # Use provided or default recipient
        recipient = to_email or self.config.to_email
        if not recipient:
            logger.error("No recipient email address provided")
            return False

        # Generate subject if not provided
        if not subject:
            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = f"Polymarket Research Report - {date_str}"

        try:
            # Create message with proper MIME structure
            message = MIMEMultipart("alternative")
            message["From"] = self.config.from_email
            message["To"] = recipient
            message["Subject"] = subject
            message["MIME-Version"] = "1.0"

            # Create plain text fallback first (lower priority)
            plain_text = self._html_to_plain_text(html_content)
            text_part = MIMEText(plain_text, "plain", "utf-8")
            text_part.add_header("Content-Type", "text/plain; charset=utf-8")
            message.attach(text_part)

            # Attach HTML content second (higher priority)
            html_part = MIMEText(html_content, "html", "utf-8")
            html_part.add_header("Content-Type", "text/html; charset=utf-8")
            message.attach(html_part)

            # Connect to SMTP server and send
            logger.info(
                f"Connecting to SMTP server {self.config.smtp_host}:{self.config.smtp_port}"
            )

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {recipient}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False

    def _html_to_plain_text(self, html: str) -> str:
        """
        Convert HTML to plain text fallback.

        Args:
            html: HTML content.

        Returns:
            Plain text version.
        """

        # Remove style and script tags
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)

        # Replace common HTML tags with text equivalents
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n\n=== \1 ===\n", text)
        text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n\n--- \1 ---\n", text)
        text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n\n\1:\n", text)
        text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n", text)
        text = re.sub(r"<li[^>]*>(.*?)</li>", r"• \1\n", text)
        text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text)
        text = re.sub(r"<em[^>]*>(.*?)</em>", r"_\1_", text)

        # Remove all other HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Clean up whitespace and add some structure
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)
        text = text.strip()

        # Add header for plain text version
        plain_text_header = "POLYMARKET RESEARCH REPORT (Plain Text Version)\n"
        plain_text_header += "=" * 50 + "\n\n"

        return plain_text_header + text


class DataLogger:
    """Logs daily run data for tracking and analysis."""

    def __init__(self):
        self.config = config.logging
        self.log_dir = self.config.data_log_dir

    def log_daily_run(self, run_data: dict) -> bool:
        """
        Log daily run data to JSON file.

        Args:
            run_data: Dictionary with run data (from DailyRun model).

        Returns:
            True if logged successfully.
        """

        try:
            # Create log directory if needed
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)

            # Generate filename with date
            date_str = run_data.get("run_date", datetime.now().isoformat())
            if isinstance(date_str, datetime):
                date_str = date_str.strftime("%Y-%m-%d")
            else:
                date_str = date_str[:10]  # Take just date part

            filename = f"{self.log_dir}/run_{date_str}.json"

            # Write JSON file
            with open(filename, "w") as f:
                json.dump(run_data, f, indent=2, default=str)

            logger.info(f"Daily run data logged to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to log daily run data: {e}")
            return False
