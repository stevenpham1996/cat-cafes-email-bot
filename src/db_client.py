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
    Uses pagination to retrieve all records beyond the default 1000 limit.
    """
    supabase = get_supabase_client()

    # Query to fetch listings and join with location tables
    query = """
        id, title, email, slug, full_address, average_rating, review_count, description, filters, thumbnail_url, price_range,
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
    
    all_listings = []
    start = 0
    batch_size = 1000
    
    while True:
        print(f"Fetching listings batch: {start} to {start + batch_size}...")
        try:
            response = (
                supabase.table("coworking_places")
                .select(query)
                .neq("email", "null")
                .range(start, start + batch_size - 1)
                .execute()
            )
            
            batch = response.data
            all_listings.extend(batch)
            
            # If we fetched fewer than batch_size, we've reached the end
            if len(batch) < batch_size:
                break
                
            start += batch_size
            
        except Exception as e:
            print(f"Error fetching batch starting at {start}: {e}")
            break
            
    return all_listings

def fetch_preview_listings(limit: int = 100) -> list[dict]:
    """
    Fetches a limited number of listings for dry-run/testing purposes.
    Does not use pagination; strictly limits the query to the specified count.
    """
    supabase = get_supabase_client()
    
    # Query to fetch listings and join with location tables
    query = """
        id, title, email, slug, full_address, average_rating, review_count, description, filters, thumbnail_url, price_range,
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
    
    print(f"Fetching preview batch of {limit} listings...")
    response = (
        supabase.table("coworking_places")
        .select(query)
        .neq("email", "null")
        .limit(limit)
        .execute()
    )
    
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
    # For now is hardcoded to 3033+
    active_users_count = 9043
    
    return {
        "platform_studios_count": studios_count,
        "platform_cities_count": cities_count,
        "platform_active_users_count": active_users_count  # Hardcoded for now per business requirements
    }
