import os
from datetime import datetime, timezone, timedelta
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
    return "id, title, email, slug, street_address, average_rating, review_count, description, filters, thumbnail_url, price_range, city_id, state_id, status, is_referral_promotion, referral_promotion_expires_at, verified_by_owner"


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
    Fetches active (status = 'approved') listings that DO NOT have an active referral promotion
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
                    .eq("is_referral_promotion", False)
                    .or_(f"referral_promotion_expires_at.is.null,referral_promotion_expires_at.lte.{now_iso}")
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
                    .eq("is_referral_promotion", False)
                    .or_(f"referral_promotion_expires_at.is.null,referral_promotion_expires_at.lte.{now_iso}")
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
                    .eq("is_referral_promotion", False)
                    .or_(f"referral_promotion_expires_at.is.null,referral_promotion_expires_at.lte.{now_iso}")
                    .range(start, start + batch_size - 1)
                    .execute().data
                )

            # Skip listings that already have an active referral promotion
            batch = [l for l in batch if not is_active_referral_promotion(l)]

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
    Fetches a limited number of active approved listings without an active referral promotion
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
            .eq("is_referral_promotion", False)
            .or_(f"referral_promotion_expires_at.is.null,referral_promotion_expires_at.lte.{now_iso}")
            .in_("cities.country_id", country_ids)
            .limit(limit).execute().data
        )

        batch_b = (
            supabase.table("coworking_places")
            .select(_QUERY_STATE)
            .not_.is_("email", "null").neq("email", "")
            .eq("status", "approved")
            .eq("is_referral_promotion", False)
            .or_(f"referral_promotion_expires_at.is.null,referral_promotion_expires_at.lte.{now_iso}")
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
            .eq("is_referral_promotion", False)
            .or_(f"referral_promotion_expires_at.is.null,referral_promotion_expires_at.lte.{now_iso}")
            .limit(limit).execute().data
        )

    return [l for l in batch if not is_active_referral_promotion(l)]

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
    from datetime import datetime, timezone, timedelta

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


def _parse_sent_at(ts: any) -> datetime | None:
    """Safely parses timestamp string or datetime object into timezone-aware datetime."""
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        clean_ts = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def fetch_email_tracking_history() -> dict[str, dict[str, datetime]]:
    """
    Fetches all successful email tracking records (status = 'sent')
    and returns an in-memory dictionary mapping:
        { listing_id: { email_description: sent_at_datetime } }
    Uses pagination to retrieve all records and avoids N+1 queries.
    """
    supabase = get_supabase_client()
    tracking_history: dict[str, dict[str, datetime]] = {}
    start = 0
    batch_size = 1000

    while True:
        try:
            response = (
                supabase.table("email_tracking")
                .select("listing_id, email_description, sent_at, status")
                .eq("status", "sent")
                .not_.is_("listing_id", "null")
                .range(start, start + batch_size - 1)
                .execute()
            )
            rows = response.data or []
            for row in rows:
                lid = str(row.get("listing_id"))
                desc = row.get("email_description") or ""
                sent_at = _parse_sent_at(row.get("sent_at"))
                if not lid or not desc or not sent_at:
                    continue
                if lid not in tracking_history:
                    tracking_history[lid] = {}
                existing = tracking_history[lid].get(desc)
                if not existing or sent_at > existing:
                    tracking_history[lid][desc] = sent_at

            if len(rows) < batch_size:
                break
            start += batch_size
        except Exception as e:
            print(f"Error fetching email tracking history batch starting at {start}: {e}")
            break

    return tracking_history


def fetch_pending_claim_listing_ids() -> set[str]:
    """
    Fetches IDs of listings that have active claims currently undergoing review
    (status in 'pending' or 'needs_more_info') to prevent sending claim follow-up
    reminders to business owners who have already submitted verification documents.
    """
    supabase = get_supabase_client()
    pending_ids: set[str] = set()
    start = 0
    batch_size = 1000

    while True:
        try:
            response = (
                supabase.table("listing_claims")
                .select("coworking_place_id, status")
                .in_("status", ["pending", "needs_more_info"])
                .not_.is_("coworking_place_id", "null")
                .range(start, start + batch_size - 1)
                .execute()
            )
            rows = response.data or []
            for row in rows:
                c_id = row.get("coworking_place_id")
                if c_id:
                    pending_ids.add(str(c_id))

            if len(rows) < batch_size:
                break
            start += batch_size
        except Exception as e:
            print(f"Error fetching pending listing claims batch starting at {start}: {e}")
            break

    return pending_ids


def fetch_all_approved_candidate_listings(country_ids: list[str] = None) -> list[dict]:
    """
    Fetches all approved listings with a valid email address across the 3 location patterns,
    regardless of promotion status, to serve as the candidate pool for follow-up evaluation.
    """
    supabase = get_supabase_client()
    all_listings = []
    start = 0
    batch_size = 1000

    while True:
        try:
            if country_ids:
                # Query A: Cases 1 & 2 — cities!inner forces country match via cities.country_id
                batch_a = (
                    supabase.table("coworking_places")
                    .select(_QUERY_CITY.format(cities_join="cities!inner"))
                    .not_.is_("email", "null").neq("email", "")
                    .eq("status", "approved")
                    .in_("cities.country_id", country_ids)
                    .range(start, start + batch_size - 1)
                    .execute().data or []
                )

                # Query B: Case 3 — states!inner forces country match via states.country_id
                batch_b = (
                    supabase.table("coworking_places")
                    .select(_QUERY_STATE)
                    .not_.is_("email", "null").neq("email", "")
                    .eq("status", "approved")
                    .is_("city_id", "null")
                    .in_("states.country_id", country_ids)
                    .range(start, start + batch_size - 1)
                    .execute().data or []
                )

                seen = {r["id"] for r in batch_a}
                batch = batch_a + [r for r in batch_b if r["id"] not in seen]
            else:
                batch = (
                    supabase.table("coworking_places")
                    .select(_QUERY_ALL)
                    .not_.is_("email", "null").neq("email", "")
                    .eq("status", "approved")
                    .range(start, start + batch_size - 1)
                    .execute().data or []
                )

            all_listings.extend(batch)
            if len(batch) < batch_size:
                break
            start += batch_size

        except Exception as e:
            print(f"Error fetching candidate listings starting at {start}: {e}")
            break

    return all_listings


def _get_location_remaining_slots(listing: dict, capacity_cache: dict) -> int:
    """Helper to extract remaining free promotion slots from the capacity cache for a listing."""
    if not capacity_cache:
        return 999  # Default if cache not provided

    city_data = listing.get("cities")
    state_data = listing.get("states")

    if city_data and isinstance(city_data, dict):
        city_id = city_data.get("id")
        if city_id and capacity_cache.get("city"):
            stats = capacity_cache["city"].get(city_id)
            if stats:
                return stats.get("remaining_free_slots", 0)
    elif state_data and isinstance(state_data, dict):
        state_id = state_data.get("id")
        if state_id and capacity_cache.get("state"):
            stats = capacity_cache["state"].get(state_id)
            if stats:
                return stats.get("remaining_free_slots", 0)

    return 0


def fetch_follow_up_listings(
    pursuit_type: str = "all",
    country_ids: list[str] = None,
    min_days: int = 3,
    force: bool = False,
    capacity_cache: dict = None,
    tracking_history: dict[str, dict[str, datetime]] = None,
    pending_claims: set[str] = None
) -> list[dict]:
    """
    Fetches approved listings that are eligible for a follow-up campaign
    based on pursuit_type ('claim', 'promotion', or 'all').

    Eligibility criteria:
    1. Must have already received Initial Outreach ('Marketing Outreach').
    2. Must satisfy cooldown interval (now - initial_sent_at >= min_days) unless force=True.
    3. For 'claim':
       - verified_by_owner is False
       - Has not already received 'Follow-up Claim Outreach'
       - Not in pending_claims set (status in 'pending' or 'needs_more_info')
    4. For 'promotion':
       - is_active_referral_promotion is False
       - Has not already received 'Follow-up Promotion Outreach'
       - Location has remaining_free_slots > 0
    5. For 'all':
       - Smart routing prioritizing claim first (if unverified and not pending),
         then promotion (if unpromoted, capacity available, and cooled off from claim follow-up).
    """
    if tracking_history is None:
        tracking_history = fetch_email_tracking_history()

    if pending_claims is None and pursuit_type in ("claim", "all"):
        pending_claims = fetch_pending_claim_listing_ids()
    elif pending_claims is None:
        pending_claims = set()

    raw_candidates = fetch_all_approved_candidate_listings(country_ids=country_ids)
    eligible_listings = []
    now = datetime.now(timezone.utc)
    cooldown = timedelta(days=min_days)

    for listing in raw_candidates:
        listing_id = str(listing.get("id"))
        history = tracking_history.get(listing_id, {})

        # Rule 1: Initial outreach must have been sent
        initial_sent_at = history.get("Marketing Outreach")
        if not initial_sent_at:
            continue

        # Rule 2: Minimum cooling-off days since initial outreach
        if not force and (now - initial_sent_at) < cooldown:
            continue

        assigned_pursuit = None

        if pursuit_type == "claim":
            # Must not have received claim follow-up yet
            if "Follow-up Claim Outreach" in history:
                continue
            # Must not already be verified
            if listing.get("verified_by_owner") is True:
                continue
            # Must not be undergoing claim review
            if listing_id in pending_claims:
                continue
            assigned_pursuit = "claim"

        elif pursuit_type == "promotion":
            # Must not have received promotion follow-up yet
            if "Follow-up Promotion Outreach" in history:
                continue
            # Must not currently have an active referral promotion
            if listing.get("is_referral_promotion") is True:
                continue
            # Must have remaining free promotion slots in its location
            remaining_slots = _get_location_remaining_slots(listing, capacity_cache)
            if remaining_slots <= 0:
                continue
            assigned_pursuit = "promotion"

        elif pursuit_type == "all":
            # Smart Routing:
            # 1. First priority: Claim (if unverified, not in pending claims, and no claim follow-up sent yet)
            has_claim_followup = "Follow-up Claim Outreach" in history
            is_verified = listing.get("verified_by_owner") is True
            is_pending_claim = listing_id in pending_claims

            if not is_verified and not is_pending_claim and not has_claim_followup:
                assigned_pursuit = "claim"
            else:
                # 2. Second priority: Promotion
                has_promo_followup = "Follow-up Promotion Outreach" in history
                is_promoted = listing.get("is_referral_promotion") is True

                if not is_promoted and not has_promo_followup:
                    # Check cooling-off interval from claim follow-up if it was sent
                    claim_followup_at = history.get("Follow-up Claim Outreach")
                    if claim_followup_at and not force and (now - claim_followup_at) < cooldown:
                        continue  # Wait for cooldown after claim follow-up

                    # Check location remaining capacity
                    remaining_slots = _get_location_remaining_slots(listing, capacity_cache)
                    if remaining_slots > 0:
                        assigned_pursuit = "promotion"

        if assigned_pursuit:
            listing["assigned_pursuit"] = assigned_pursuit
            eligible_listings.append(listing)

    return eligible_listings

