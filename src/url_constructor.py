from src.localization import get_locale_for_listing

def construct_listing_url(listing: dict) -> str | None:
    """
    Constructs the URL for a listing based on its location data.
    New Format: /{locale}/{country_slug}/{state_slug}/{city_slug}/{listing_slug}
    
    Args:
        listing (dict): A dictionary containing listing and location data 
                        as returned by fetch_listings().
                        
    Returns:
        str: The constructed URL path (e.g., /vi/vietnam/hanoi/listing-slug).
             Returns None if essential data is missing.
    """
    try:
        listing_slug = listing.get("slug")
        city_data = listing.get("cities")
        
        if not listing_slug or not city_data:
            return None
            
        city_slug = city_data.get("slug")
        state_id = city_data.get("state_id")
        
        # Determine Locale prefix
        locale = get_locale_for_listing(listing)
        if not locale:
            return None
        
        # Get Country Slug from City's relation
        # Get Country Slug from City's relation
        country_data = city_data.get("countries")
        if not country_data:
            return None
        country_slug = country_data.get("slug")

        if not country_slug:
            return None

        # Case 1: With State
        # Path: /{locale}/{country_slug}/{state_slug}/{city_slug}/{listing_slug}
        if state_id:
            state_data = city_data.get("states")
            if not state_data:
                return None
                
            state_slug = state_data.get("slug")
            if not state_slug:
                return None
            
            return f"/{locale}/{country_slug}/{state_slug}/{city_slug}/{listing_slug}"
            
        # Case 2: Without State
        # Path: /{locale}/{country_slug}/{city_slug}/{listing_slug}
        else:
            return f"/{locale}/{country_slug}/{city_slug}/{listing_slug}"
            
    except Exception as e:
        # Log error if needed, for now just return None or re-raise
        print(f"Error constructing URL for listing {listing.get('id')}: {e}")
        return None
