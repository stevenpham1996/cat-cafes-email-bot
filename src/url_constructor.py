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
        if not listing_slug:
            return None

        locale = get_locale_for_listing(listing)
        if not locale:
            return None

        city_data = listing.get("cities")

        # Case 3: City-less — coworking_places.state_id → states → countries
        if not city_data:
            state_data = listing.get("states")
            if not state_data:
                return None
            state_slug = state_data.get("slug")
            country_slug = (state_data.get("countries") or {}).get("slug")
            if not state_slug or not country_slug:
                return None
            return f"/{locale}/{country_slug}/{state_slug}/{listing_slug}"

        # Cases 1 & 2: City-based
        city_slug = city_data.get("slug")
        country_data = city_data.get("countries")
        if not country_data:
            return None
        country_slug = country_data.get("slug")
        if not city_slug or not country_slug:
            return None

        state_id = city_data.get("state_id")

        # Case 1: With State
        if state_id:
            state_data = city_data.get("states")
            if not state_data:
                return None
            state_slug = state_data.get("slug")
            if not state_slug:
                return None
            return f"/{locale}/{country_slug}/{state_slug}/{city_slug}/{listing_slug}"

        # Case 2: Without State
        return f"/{locale}/{country_slug}/{city_slug}/{listing_slug}"

    except Exception as e:
        print(f"Error constructing URL for listing {listing.get('id')}: {e}")
        return None
