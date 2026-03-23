import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dotenv import load_dotenv
import logging
import requests
from premailer import transform

load_dotenv()

# Configuration
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT") or 587)
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")

import json

# Jinja2 Environment Cache
_ENV_CACHE = {}
_DASHBOARD_TRANSLATIONS = None

def load_dashboard_translations():
    """Loads dashboard translations from JSON file."""
    global _DASHBOARD_TRANSLATIONS
    if _DASHBOARD_TRANSLATIONS is not None:
        return _DASHBOARD_TRANSLATIONS
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(os.path.dirname(current_dir), "translations", "dashboard.json")
        with open(json_path, "r", encoding="utf-8") as f:
            _DASHBOARD_TRANSLATIONS = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load dashboard translations: {e}")
        _DASHBOARD_TRANSLATIONS = {}
    return _DASHBOARD_TRANSLATIONS

def get_template_env(template_dir: str):
    """Gets or creates a Jinja2 environment for the given template directory."""
    if template_dir in _ENV_CACHE:
        return _ENV_CACHE[template_dir]
    
    # Always include the base 'templates' directory for shared partials
    search_paths = [template_dir]
    if template_dir != "templates":
        search_paths.append("templates")
    
    loader = FileSystemLoader(searchpath=search_paths)
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    _ENV_CACHE[template_dir] = env
    return env

def render_email_html(context: dict, template_name: str, template_dir: str = "templates", target_lang: str = "en") -> str:
    """
    Renders the HTML email template with the provided context.
    
    Args:
        context (dict): Dictionary containing data for the template.
        template_name (str): The name of the template file to use.
        template_dir (str): The directory to search for templates.
        target_lang (str): The target language code for localization.
        
    Returns:
        str: Rendered HTML string.
    """
    # Load translations and add to context if not already present
    if 't' not in context:
        translations = load_dashboard_translations()
        context['t'] = translations.get(target_lang, translations.get("en", {}))

    env = get_template_env(template_dir)
    template = env.get_template(template_name)
    return template.render(**context)

def send_email(recipient: str, subject: str, context: dict, template_name: str, template_dir: str = "templates", target_lang: str = "en") -> bool:
    """
    Sends an email using SMTP and Jinja2 templating with inlined CSS.
    
    Args:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        context (dict): Dictionary containing data for the template.
        template_name (str): The name of the template file to use.
        template_dir (str): The directory to search for templates.
        target_lang (str): The target language code for localization.
        
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL]):
        print("Error: Missing SMTP configuration in environment variables.")
        return False

    try:
        # 1. Render HTML content
        rendered_html = render_email_html(context, template_name, template_dir, target_lang)
        
        # 2. Use premailer to inline internal CSS
        inlined_html = transform(rendered_html, disable_validation=True, cssutils_logging_level=logging.CRITICAL)

        # Create Plain Text Fallback
        text_content = f"""
            Hi {context.get('title', 'Partner')},

            We noticed your cafe on our directory and would love to help you reach more cat lovers.
            We have created a dedicated listing page for your business.

            Details:
            Address: {context.get('street_address', 'N/A')}
            Rating: {context.get('average_rating', 'N/A')} ({context.get('review_count', 0)} reviews)
            Description: {context.get('description', 'N/A')[:100]}...

            You can view and claim it here:

            {context.get('listing_url', '#')}

            Claiming your listing allows you to update your information, add photos, and connect with our community.

            Best regards,
            The Cat Cafe Directory Team
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
