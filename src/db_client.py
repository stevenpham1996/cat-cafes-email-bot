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

def resolve_country_ids(terms: list[str]) -> list[str]:
    """
    Resolves a list of country terms (codes, slugs, or names) to their database UUIDs.
    Logic:
    1. Check for matches in 'code' (case-insensitive) or 'slug' (exact).
    2. If not found, check for matches in 'name' (case-insensitive).
    """
    if not terms:
        return []

    supabase = get_supabase_client()
    
    # Fetch all countries to perform resolution in Python (efficient for ~250 records)
    try:
        response = supabase.table("countries").select("id, name, code, slug").execute()
        countries = response.data
    except Exception as e:
        print(f"Error fetching countries for resolution: {e}")
        return []

    resolved_ids = []
    terms = [t.strip().lower() for t in terms if t.strip()]
    
    for term in terms:
        match_id = None
        
        # 1. Try matching by code or slug (reference-first)
        for country in countries:
            code = (country.get("code") or "").lower()
            slug = (country.get("slug") or "").lower()
            if term == code or term == slug:
                match_id = country["id"]
                break
        
        # 2. Try matching by name (fallback)
        if not match_id:
            for country in countries:
                name = (country.get("name") or "").lower()
                if term == name:
                    match_id = country["id"]
                    break
        
        if match_id:
            if match_id not in resolved_ids:
                resolved_ids.append(match_id)
        else:
            print(f"Warning: Could not resolve country term '{term}'. Skipping.")

    return resolved_ids

def fetch_listings(country_ids: list[str] = None) -> list[dict]:
    """
    Fetches listings from the database with their associated location data.
    Joins with cities, states, and countries tables.
    Filters for listings with a valid email address and optionally by country.
    Uses pagination to retrieve all records beyond the default 1000 limit.
    """
    supabase = get_supabase_client()

    # Use !inner join for cities if we are filtering by country
    cities_join = "cities!inner" if country_ids else "cities"
    
    # Query to fetch listings and join with location tables
    # Includes states.countries to support the priority determination logic
    query = f"""
        id, title, email, slug, street_address, average_rating, review_count, description, filters, thumbnail_url, price_range,
        {cities_join} (
            slug,
            state_id,
            country_id,
            states (
                slug,
                countries (
                    code
                )
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
            builder = (
                supabase.table("coworking_places")
                .select(query)
                .not_.is_("email", "null")
                .neq("email", "")
            )
            
            # Apply Country Filter
            if country_ids:
                # Simplified logic: Use cities.country_id directly.
                # This assumes cities.country_id is always correctly set, which is
                # standard for this database schema.
                ids_str = ",".join(country_ids)
                builder = builder.in_("cities.country_id", country_ids)

            response = builder.range(start, start + batch_size - 1).execute()
            
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

def fetch_preview_listings(limit: int = 100, country_ids: list[str] = None) -> list[dict]:
    """
    Fetches a limited number of listings for dry-run/testing purposes.
    Does not use pagination; strictly limits the query to the specified count.
    """
    supabase = get_supabase_client()
    
    # Use !inner join for cities if we are filtering by country
    cities_join = "cities!inner" if country_ids else "cities"
    
    # Query to fetch listings and join with location tables
    # Includes states.countries to support the priority determination logic
    query = f"""
        id, title, email, slug, street_address, average_rating, review_count, description, filters, thumbnail_url, price_range,
        {cities_join} (
            slug,
            state_id,
            country_id,
            states (
                slug,
                countries (
                    code
                )
            ),
            countries (
                slug,
                code
            )
        )
    """
    
    print(f"Fetching preview batch of {limit} listings...")
    builder = (
        supabase.table("coworking_places")
        .select(query)
        .not_.is_("email", "null")
        .neq("email", "")
    )
    
    # Apply Country Filter
    if country_ids:
        # Simplified logic: Use cities.country_id directly.
        # This assumes cities.country_id is always correctly set.
        builder = builder.in_("cities.country_id", country_ids)

    response = builder.limit(limit).execute()
    
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
    active_users_count = 25972
    
    return {
        "platform_studios_count": studios_count,
        "platform_cities_count": cities_count,
        "platform_active_users_count": active_users_count  # Hardcoded for now per business requirements
    }
