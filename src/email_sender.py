import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dotenv import load_dotenv

load_dotenv()

# Configuration
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

# Setup Jinja2 Environment
template_loader = FileSystemLoader(searchpath="templates")
template_env = Environment(
    loader=template_loader,
    autoescape=select_autoescape(['html', 'xml'])
)

def send_email(recipient: str, subject: str, context: dict) -> bool:
    """
    Sends an email using SMTP and Jinja2 templating.
    
    Args:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        context (dict): Dictionary containing data for the template (e.g., {'title': '...', 'url': '...'}).
        
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL]):
        print("Error: Missing SMTP configuration in environment variables.")
        return False

    try:
        # Render HTML content
        template = template_env.get_template("email_template.html")
        html_content = template.render(**context)
        
        # Create Plain Text Fallback
        text_content = f"""
Hi {context.get('title', 'Partner')},

We noticed your studio on our directory and would love to help you reach more yoga enthusiasts.
We have created a dedicated listing page for your business. You can view and claim it here:

{context.get('url', '#')}

Claiming your listing allows you to update your information, add photos, and connect with our community.

Best regards,
The Hot Yoga Studios Team
        """

        # Create MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = recipient

        # Attach parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Create secure connection with server and send email
        context_ssl = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context_ssl)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
            
        print(f"Successfully sent email to {recipient}")
        return True

    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")
        return False
