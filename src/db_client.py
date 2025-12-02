import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client.
    """
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in environment variables.")

    return create_client(url, key)

def fetch_listings() -> list[dict]:
    """
    Fetches listings from the database with their associated location data.
    Joins with cities, states, and countries tables.
    Filters for listings with a valid email address.
    """
    supabase = get_supabase_client()

    # Query to fetch listings and join with location tables
    # We fetch cities, and from cities we fetch states and countries.
    # We rely on cities.country_id for the country slug in all cases.
    
    query = """
        id, title, email, slug, full_address, average_rating, review_count, description, filters, thumbnail_url,
        cities (
            slug,
            state_id,
            country_id,
            states (
                slug
            ),
            countries (
                slug,
                code
            )
        )
    """
    
    response = supabase.table("coworking_places").select(query).neq("email", "null").execute()
    
    return response.data
