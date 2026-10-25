import os
import smtplib
import urllib.parse
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_or_compose_email(to_email: str, subject: str, body: str) -> str:
    """
    Sends an email directly if SMTP credentials are configured in .env,
    or opens Gmail / Windows Mail compose window with recipient, subject, and body prefilled.
    
    Args:
        to_email: Recipient email address
        subject: Subject line of the email
        body: Body message content of the email
    """
    smtp_email = os.getenv("SMTP_EMAIL", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    
    # 1. Direct Background SMTP Sending (if configured in .env)
    if smtp_email and smtp_password:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Default to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            server.quit()
            return f"Email successfully sent directly to {to_email}."
        except Exception as e:
            print(f"SMTP error: {e}. Falling back to browser compose.")
            
    # 2. Browser / Default Mail Client Fallback
    # Opens Gmail compose or mailto link directly in the user's browser
    try:
        encoded_subject = urllib.parse.quote(subject)
        encoded_body = urllib.parse.quote(body)
        
        # Open Gmail web compose directly
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to_email}&su={encoded_subject}&body={encoded_body}"
        webbrowser.open(gmail_url)
        return f"Opened Gmail draft ready to send to {to_email} with subject '{subject}'."
    except Exception as e:
        # Mailto fallback
        mailto_url = f"mailto:{to_email}?subject={encoded_subject}&body={encoded_body}"
        webbrowser.open(mailto_url)
        return f"Opened default Mail client for {to_email}."
