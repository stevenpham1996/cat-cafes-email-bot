import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dotenv import load_dotenv
import requests
from premailer import transform

load_dotenv()

# Configuration
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT") or 587)
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

# Setup Jinja2 Environment
template_loader = FileSystemLoader(searchpath="templates")
template_env = Environment(
    loader=template_loader,
    autoescape=select_autoescape(['html', 'xml'])
)

def render_email_html(context: dict, template_name: str = "hotyoga_email_template_en.html") -> str:
    """
    Renders the HTML email template with the provided context.
    
    Args:
        context (dict): Dictionary containing data for the template.
        template_name (str): The name of the template file to use.
        
    Returns:
        str: Rendered HTML string.
    """
    template = template_env.get_template(template_name)
    return template.render(**context)

def send_email(recipient: str, subject: str, context: dict, template_name: str = "hotyoga_email_template_en.html") -> bool:
    """
    Sends an email using SMTP and Jinja2 templating with inlined CSS.
    
    Args:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        context (dict): Dictionary containing data for the template (e.g., {'title': '...', 'url': '...'}).
        template_name (str): The name of the template file to use.
        
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL]):
        print("Error: Missing SMTP configuration in environment variables.")
        return False

    try:
        # 1. Render HTML content
        rendered_html = render_email_html(context, template_name)
        
        # 2. Use premailer to inline internal CSS (from <style> block)
        # We no longer fetch external Tailwind CSS as the templates now use robust inline styles.
        inlined_html = transform(rendered_html)

        # Create Plain Text Fallback
        text_content = f"""
            Hi {context.get('title', 'Partner')},

            We noticed your studio on our directory and would love to help you reach more yoga enthusiasts.
            We have created a dedicated listing page for your business.

            Details:
            Address: {context.get('full_address', 'N/A')}
            Rating: {context.get('average_rating', 'N/A')} ({context.get('review_count', 0)} reviews)
            Description: {context.get('description', 'N/A')[:100]}...

            You can view and claim it here:

            {context.get('listing_url', '#')}

            Claiming your listing allows you to update your information, add photos, and connect with our community.

            Best regards,
            The Hot Yoga Studios Team
        """

        # Create MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = recipient

        # Attach parts - plain text and the new inlined HTML
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(inlined_html, "html")
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
