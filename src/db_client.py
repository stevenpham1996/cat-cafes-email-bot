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

def _base_fields():
    """Shared scalar fields for all listing queries."""
    return "id, title, email, slug, street_address, average_rating, review_count, description, filters, thumbnail_url, price_range, city_id, state_id, status, is_referral_promotion, referral_promotion_expires_at"


# Query for Cases 1 & 2 (city-based listings). cities join can be !inner or plain.
_QUERY_CITY = _base_fields() + """,
    {cities_join} (
        id,
        name,
        slug,
        state_id,
        country_id,
        states (
            id,
            name,
            slug,
            countries ( id, name, code )
        ),
        countries ( id, name, slug, code )
    ),
    states ( id, name, slug, countries ( id, name, slug, code ) )
"""

# Query for Case 3 (city-less listings). states join is always !inner when filtering.
_QUERY_STATE = _base_fields() + """,
    cities ( id, name, slug, state_id, country_id, states ( id, name, slug, countries ( id, name, code ) ), countries ( id, name, slug, code ) ),
    states!inner ( id, name, slug, countries ( id, name, slug, code ) )
"""

# No-filter query: plain left joins on both cities and states.
_QUERY_ALL = _base_fields() + """,
    cities ( id, name, slug, state_id, country_id, states ( id, name, slug, countries ( id, name, code ) ), countries ( id, name, slug, code ) ),
    states ( id, name, slug, countries ( id, name, slug, code ) )
"""

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

from datetime import datetime, timezone

def is_active_referral_promotion(listing: dict) -> bool:
    """
    Evaluates whether a listing has an active referral promotion:
    Condition 1: is_referral_promotion is True
    Condition 2: OR referral_promotion_expires_at is in the future (> NOW)
    """
    if listing.get("is_referral_promotion") is True:
        return True

    expires_at_str = listing.get("referral_promotion_expires_at")
    if expires_at_str:
        try:
            clean_ts = str(expires_at_str).replace("Z", "+00:00")
            expires_at = datetime.fromisoformat(clean_ts)
            if expires_at > datetime.now(timezone.utc):
                return True
        except Exception:
            pass
    return False

def fetch_listings(country_ids: list[str] = None) -> list[dict]:
    """
    Fetches active (status = 'approved') listings that have an active referral promotion
    (is_referral_promotion is True OR referral_promotion_expires_at > NOW)
    from the database with their associated location data.
    Joins with cities, states, and countries tables.
    Filters for listings with a valid email address and optionally by country.
    Uses pagination to retrieve all records beyond the default 1000 limit.
    """
    supabase = get_supabase_client()
    all_listings = []
    start = 0
    batch_size = 1000
    now_iso = datetime.now(timezone.utc).isoformat()

    while True:
        print(f"Fetching listings batch: {start} to {start + batch_size}...")
        try:
            if country_ids:
                # Query A: Cases 1 & 2 — cities!inner forces country match via cities.country_id
                batch_a = (
                    supabase.table("coworking_places")
                    .select(_QUERY_CITY.format(cities_join="cities!inner"))
                    .not_.is_("email", "null").neq("email", "")
                    .eq("status", "approved")
                    .or_(f"is_referral_promotion.eq.true,referral_promotion_expires_at.gt.{now_iso}")
                    .in_("cities.country_id", country_ids)
                    .range(start, start + batch_size - 1)
                    .execute().data
                )

                # Query B: Case 3 — states!inner forces country match via states.country_id
                batch_b = (
                    supabase.table("coworking_places")
                    .select(_QUERY_STATE)
                    .not_.is_("email", "null").neq("email", "")
                    .eq("status", "approved")
                    .or_(f"is_referral_promotion.eq.true,referral_promotion_expires_at.gt.{now_iso}")
                    .is_("city_id", "null")
                    .in_("states.country_id", country_ids)
                    .range(start, start + batch_size - 1)
                    .execute().data
                )

                seen = {r["id"] for r in batch_a}
                batch = batch_a + [r for r in batch_b if r["id"] not in seen]
            else:
                batch = (
                    supabase.table("coworking_places")
                    .select(_QUERY_ALL)
                    .not_.is_("email", "null").neq("email", "")
                    .eq("status", "approved")
                    .or_(f"is_referral_promotion.eq.true,referral_promotion_expires_at.gt.{now_iso}")
                    .range(start, start + batch_size - 1)
                    .execute().data
                )

            # Validate active referral promotion status in Python
            batch = [l for l in batch if is_active_referral_promotion(l)]

            all_listings.extend(batch)
            if len(batch) < batch_size:
                break
            start += batch_size

        except Exception as e:
            print(f"Error fetching batch starting at {start}: {e}")
            break

    return all_listings

def fetch_preview_listings(limit: int = 100, country_ids: list[str] = None) -> list[dict]:
    """
    Fetches a limited number of active approved listings with an active referral promotion
    for dry-run/testing purposes.
    """
    supabase = get_supabase_client()
    print(f"Fetching preview batch of {limit} listings...")
    now_iso = datetime.now(timezone.utc).isoformat()

    if country_ids:
        batch_a = (
            supabase.table("coworking_places")
            .select(_QUERY_CITY.format(cities_join="cities!inner"))
            .not_.is_("email", "null").neq("email", "")
            .eq("status", "approved")
            .or_(f"is_referral_promotion.eq.true,referral_promotion_expires_at.gt.{now_iso}")
            .in_("cities.country_id", country_ids)
            .limit(limit).execute().data
        )

        batch_b = (
            supabase.table("coworking_places")
            .select(_QUERY_STATE)
            .not_.is_("email", "null").neq("email", "")
            .eq("status", "approved")
            .or_(f"is_referral_promotion.eq.true,referral_promotion_expires_at.gt.{now_iso}")
            .is_("city_id", "null")
            .in_("states.country_id", country_ids)
            .limit(limit).execute().data
        )

        seen = {r["id"] for r in batch_a}
        batch = batch_a + [r for r in batch_b if r["id"] not in seen]
    else:
        batch = (
            supabase.table("coworking_places")
            .select(_QUERY_ALL)
            .not_.is_("email", "null").neq("email", "")
            .eq("status", "approved")
            .or_(f"is_referral_promotion.eq.true,referral_promotion_expires_at.gt.{now_iso}")
            .limit(limit).execute().data
        )

    return [l for l in batch if is_active_referral_promotion(l)]

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

def fetch_approved_listings_for_cache() -> list[dict]:
    """
    Fetches all approved listings from the database with only the columns needed
    to calculate capacity limits.
    """
    supabase = get_supabase_client()
    all_listings = []
    start = 0
    batch_size = 1000

    while True:
        try:
            batch = (
                supabase.table("coworking_places")
                .select("id, city_id, state_id, is_featured, is_referral_promotion, referral_promotion_expires_at")
                .eq("status", "approved")
                .range(start, start + batch_size - 1)
                .execute().data
            )
            all_listings.extend(batch)
            if len(batch) < batch_size:
                break
            start += batch_size
        except Exception as e:
            print(f"Error fetching approved listings for cache: {e}")
            break

    return all_listings

def calculate_capacity_limits_cache(listings_data: list[dict]) -> dict:
    """
    Processes all approved listings to calculate the promotion stats
    for each city and each no-city state.
    
    Returns a dictionary of:
    {
        "city": {
            city_id: {
                "N": total_active,
                "P": active_paid,
                "R": active_free,
                "L": max_paid_slots,
                "remaining_free_slots": remaining_free_slots
            }
        },
        "state": {
            state_id: {
                "N": total_active,
                "P": active_paid,
                "R": active_free,
                "L": max_paid_slots,
                "remaining_free_slots": remaining_free_slots
            }
        }
    }
    """
    import math
    from datetime import datetime, timezone

    # Current time in UTC for checking promotion expiration
    now = datetime.now(timezone.utc)

    city_stats = {}
    state_stats = {}

    for item in listings_data:
        city_id = item.get("city_id")
        state_id = item.get("state_id")
        is_featured = bool(item.get("is_featured"))
        is_referral_promotion = bool(item.get("is_referral_promotion"))
        
        # Check if referral promotion is active (expires_at > now)
        expires_at_str = item.get("referral_promotion_expires_at")
        is_referral_active = False
        if is_referral_promotion and expires_at_str:
            try:
                # Parse ISO timestamp, e.g. "2026-07-29T18:54:14+00:00" or with Z
                clean_ts = expires_at_str.replace("Z", "+00:00")
                expires_at = datetime.fromisoformat(clean_ts)
                if expires_at > now:
                    is_referral_active = True
            except Exception:
                is_referral_active = False

        if city_id:
            if city_id not in city_stats:
                city_stats[city_id] = {"N": 0, "P": 0, "R": 0}
            city_stats[city_id]["N"] += 1
            if is_featured:
                city_stats[city_id]["P"] += 1
            if is_referral_active:
                city_stats[city_id]["R"] += 1
        elif state_id:
            # No-city State (city_id is None)
            if state_id not in state_stats:
                state_stats[state_id] = {"N": 0, "P": 0, "R": 0}
            state_stats[state_id]["N"] += 1
            if is_featured:
                state_stats[state_id]["P"] += 1
            if is_referral_active:
                state_stats[state_id]["R"] += 1

    def compute_limits(stats):
        result = {}
        for loc_id, s in stats.items():
            N = s["N"]
            P = s["P"]
            R = s["R"]
            
            # Tiered Step Function for Limit (L)
            if N < 5:
                L = 1
            elif N <= 50:
                L = math.ceil(0.1 * N)
                if L < 1:
                    L = 1
            else:
                L = 8
                
            # Remaining Free Slots = max(0, (L * 2) - ((P * 2) + R))
            remaining_free_slots = max(0, (L * 2) - ((P * 2) + R))
            
            result[loc_id] = {
                "N": N,
                "P": P,
                "R": R,
                "L": L,
                "remaining_free_slots": remaining_free_slots
            }
        return result

    return {
        "city": compute_limits(city_stats),
        "state": compute_limits(state_stats)
    }

