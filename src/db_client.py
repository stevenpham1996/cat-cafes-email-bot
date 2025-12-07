import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client.
    """
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SECRET_KEY")

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

def get_platform_stats() -> dict:
    """
    Fetches platform statistics for email templates.
    Returns a dictionary with:
    - platform_studios_count (int)
    - platform_cities_count (int)
    - platform_active_users_count (str)
    """
    supabase = get_supabase_client()
    
    # 1. Get Studios Count (Head request for exact count)
    # select("*", count="exact", head=True) returns the count without the data rows
    studios_response = supabase.table("coworking_places").select("*", count="exact", head=True).execute()
    studios_count = studios_response.count if studios_response.count is not None else 0
    
    # 2. Get Unique Cities Count
    # Fetch all city_ids to count unique ones in Python
    cities_response = supabase.table("cities").select("*", count="exact", head=True).execute()
    # unique_cities = {item['city_id'] for item in cities_response.data if item.get('city_id')}
    cities_count = cities_response.count if cities_response.count is not None else 0
    
    # 3. Get Active Users Count
    # For now is hardcoded to 2033+ per business requirements
    active_users_count = 2033
    
    return {
        "platform_studios_count": studios_count,
        "platform_cities_count": cities_count,
        "platform_active_users_count": active_users_count  # Hardcoded for now per business requirements
    }
