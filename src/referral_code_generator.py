"""
Helper module to generate referral HTML code snippets for email templates.
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Setup Jinja2 Environment for this module
template_loader = FileSystemLoader(searchpath="templates")
template_env = Environment(
    loader=template_loader,
    autoescape=select_autoescape(['html', 'xml'])
)

def get_badge_html_code(listing_url: str) -> str:
    """
    Returns the HTML code for the branded badge that users can copy.
    Uses the template as the Source of Truth.
    
    Args:
        listing_url: The full URL to the listing page
        
    Returns:
        str: HTML code as a string
    """
    template = template_env.get_template("hotyoga_referral_badge.html")
    return template.render(listing_url=listing_url)


def get_text_link_html_code(listing_url: str) -> str:
    """
    Returns the HTML code for the text link that users can copy.
    Uses the template as the Source of Truth.
    
    Args:
        listing_url: The full URL to the listing page
        
    Returns:
        str: HTML code as a string
    """
    template = template_env.get_template("hotyoga_referral_text.html")
    return template.render(listing_url=listing_url)
