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
    # We need to be careful with the join syntax for Supabase/PostgREST
    response = supabase.table("coworking_places").select(
        "id, title, email, slug, "
        "cities!inner(slug, country_id, state_id), "
        "cities!inner(states(slug, country_id)), "
        "cities!inner(countries(slug))"
    ).neq("email", "null").execute()
    
    # Note: The above query structure assumes standard PostgREST resource embedding.
    # However, given the complex relationship described (City -> State -> Country OR City -> Country),
    # we might need to fetch raw data and process it, or use a more complex query.
    # Let's try a slightly different approach to get all necessary data for the logic.
    
    # Revised Query Strategy:
    # Fetch coworking_places with city data.
    # Fetch city data with state and country data.
    # But Supabase allows deep nesting.
    
    # Let's try to get:
    # coworking_places -> cities -> states
    # coworking_places -> cities -> countries
    
    # The query below attempts to fetch:
    # - listing fields
    # - city fields (slug, state_id, country_id)
    # - state fields via city (slug, country_id) - purely for the "With State" path
    # - country fields via city (slug) - for "No State" path? No, country is linked to city OR state.
    
    # Actually, looking at the schema:
    # City has country_id. State has country_id.
    # If city has state_id, we use state's country? Or city's country?
    # The prompt says: 
    # "With States - coworking_places.city_id to cities.id and cities.state_id to states.id"
    # "Without States - states.country_id to countries.id (case cities.state_id is NULL, cities.country_id used directly)"
    
    # So we need:
    # 1. City slug
    # 2. State slug (if exists)
    # 3. Country slug (from State if State exists, else from City)
    
    # Let's fetch enough data to handle this in Python (safer than complex SQL/PostgREST for now).
    
    query = """
        id, title, email, slug,
        cities (
            slug,
            state_id,
            country_id,
            states (
                slug,
                country_id,
                countries (
                    slug
                )
            ),
            countries (
                slug
            )
        )
    """
    
    # Note: "countries" inside "states" gets country for state-linked cities.
    # "countries" inside "cities" gets country for direct-linked cities.
    
    response = supabase.table("coworking_places").select(query).neq("email", "null").execute()
    
    return response.data
