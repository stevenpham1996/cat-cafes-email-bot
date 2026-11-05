"""
Helper module to generate referral HTML code snippets for email templates.
"""
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Jinja2 Environment Cache
_ENV_CACHE = {}

def get_template_env(template_dir: str):
    """Gets or creates a Jinja2 environment for the given template directory."""
    norm_dir = os.path.normpath(template_dir)
    if norm_dir in _ENV_CACHE:
        return _ENV_CACHE[norm_dir]
    
    # Always include the base 'templates' directory for shared partials
    search_paths = [norm_dir]
    base_templates_dir = os.path.normpath("templates")
    if norm_dir != base_templates_dir and base_templates_dir not in search_paths:
        search_paths.append(base_templates_dir)
    
    loader = FileSystemLoader(searchpath=search_paths)
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    _ENV_CACHE[norm_dir] = env
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
