def construct_listing_url(listing: dict) -> str:
    """
    Constructs the URL for a listing based on its location data.
    
    Args:
        listing (dict): A dictionary containing listing and location data 
                        as returned by fetch_listings().
                        
    Returns:
        str: The constructed URL path (e.g., /vietnam/hanoi/listing-slug).
             Returns None if essential data is missing.
    """
    try:
        listing_slug = listing.get("slug")
        city_data = listing.get("cities")
        
        if not listing_slug or not city_data:
            return None
            
        city_slug = city_data.get("slug")
        state_id = city_data.get("state_id")
        
        # Common: Get Country Slug from City's relation
        # We simplified the query to always fetch countries via cities
        country_data = city_data.get("countries")
        if not country_data:
            return None
        country_slug = country_data.get("slug")

        # Case 1: With State
        # Path: /{country_slug}/{state_slug}/{city_slug}/{listing_slug}
        if state_id:
            state_data = city_data.get("states")
            if not state_data:
                return None
                
            state_slug = state_data.get("slug")
            
            return f"/{country_slug}/{state_slug}/{city_slug}/{listing_slug}"
            
        # Case 2: Without State
        # Path: /{country_slug}/{city_slug}/{listing_slug}
        else:
            return f"/{country_slug}/{city_slug}/{listing_slug}"
            
    except Exception as e:
        # Log error if needed, for now just return None or re-raise
        print(f"Error constructing URL for listing {listing.get('id')}: {e}")
        return None
