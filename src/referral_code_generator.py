"""
Helper module to generate referral HTML code snippets for email templates.
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Jinja2 Environment Cache
_ENV_CACHE = {}

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

def get_badge_html_code(listing_url: str, template_dir: str = "templates") -> str:
    """
    Returns the HTML code for the branded badge that users can copy.
    Uses the template as the Source of Truth.
    
    Args:
        listing_url: The full URL to the listing page
        template_dir: The directory to search for templates
        
    Returns:
        str: HTML code as a string
    """
    env = get_template_env(template_dir)
    template = env.get_template("catcafe_referral_badge.html")
    return template.render(listing_url=listing_url)


def get_text_link_html_code(listing_url: str, template_dir: str = "templates") -> str:
    """
    Returns the HTML code for the text link that users can copy.
    Uses the template as the Source of Truth.
    
    Args:
        listing_url: The full URL to the listing page
        template_dir: The directory to search for templates
        
    Returns:
        str: HTML code as a string
    """
    env = get_template_env(template_dir)
    template = env.get_template("catcafe_referral_text.html")
    return template.render(listing_url=listing_url)
