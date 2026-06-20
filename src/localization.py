"""
Centralized localization mappings for the Cat Cafe Directory.
Maps countries and slugs to their appropriate locales and handles locale defaults.
"""

# Mapping of 2-letter ISO country codes to locale codes
COUNTRY_CODE_TO_LOCALE = {
    'ca': 'en', 'ch': 'de', 'fr': 'fr', 'gb': 'en', 'us': 'en',
    'de': 'de', 'au': 'en', 'es': 'es', 'nl': 'nl', 'ie': 'en',
    'nz': 'en', 'be': 'fr', 'at': 'de', 'mx': 'es', 'ar': 'es',
    'co': 'es', 'pe': 'es', 've': 'es', 'cl': 'es', 'ec': 'es',
    'gt': 'es', 'cu': 'es', 'bo': 'es', 'hn': 'es', 'py': 'es',
    'sv': 'es', 'ni': 'es', 'cr': 'es', 'pa': 'es', 'uy': 'es',
    'pt': 'pt', 'br': 'pt', 'ao': 'pt', 'mz': 'pt', 'ru': 'ru',
    'by': 'ru', 'kz': 'ru', 'jp': 'ja', 'kr': 'ko', 'cn': 'zh',
    'hk': 'zh', 'tw': 'zh', 'id': 'id', 'vn': 'vi', 'th': 'en',
    'my': 'en', 'sg': 'en', 'ph': 'en', 'it': 'it'
}

# Mapping of normalized country slugs to locale codes
COUNTRY_SLUG_TO_LOCALE = {
    'canada': 'en', 'switzerland': 'de', 'france': 'fr',
    'united-kingdom': 'en', 'united-states': 'en', 'germany': 'de',
    'australia': 'en', 'spain': 'es', 'netherlands': 'nl',
    'ireland': 'en', 'new-zealand': 'en', 'belgium': 'fr',
    'austria': 'de', 'mexico': 'es', 'argentina': 'es',
    'colombia': 'es', 'peru': 'es', 'venezuela': 'es',
    'chile': 'es', 'ecuador': 'es', 'guatemala': 'es',
    'cuba': 'es', 'bolivia': 'es', 'honduras': 'es',
    'paraguay': 'es', 'el-salvador': 'es', 'nicaragua': 'es',
    'costa-rica': 'es', 'panama': 'es', 'uruguay': 'es',
    'portugal': 'pt', 'brazil': 'pt', 'angola': 'pt',
    'mozambique': 'pt', 'russia': 'ru', 'belarus': 'ru',
    'kazakhstan': 'ru', 'japan': 'ja', 'south-korea': 'ko',
    'china': 'zh', 'hong-kong': 'zh', 'taiwan': 'zh',
    'indonesia': 'id', 'vietnam': 'vi', 'thailand': 'en',
    'malaysia': 'en', 'singapore': 'en', 'philippines': 'en', 'italy': 'it'
}

# Mapping of locale codes to their default country code
LOCALE_TO_DEFAULT_COUNTRY = {
    'en': 'us', 'fr': 'fr', 'de': 'de', 'es': 'es', 'pt': 'pt',
    'nl': 'nl', 'ru': 'ru', 'ja': 'jp', 'ko': 'kr', 'zh': 'cn',
    'id': 'id', 'vi': 'vn', 'it': 'it'
}

def get_locale_for_listing(listing: dict) -> str:
    """
    Determines the locale for a listing based on its country code or slug.
    Supports all 3 location patterns:
      Case 1/2: country via listing['cities']['countries']
      Case 3:   country via listing['states']['countries'] (city-less)
    Defaults to 'en' if no mapping is found.
    """
    city_data = listing.get("cities") or {}
    country_data = city_data.get("countries") or {}

    # Case 3 fallback: no city, read country from top-level states join
    if not country_data:
        state_data = listing.get("states") or {}
        country_data = state_data.get("countries") or {}

    code = (country_data.get("code") or "").lower()
    slug = (country_data.get("slug") or "").lower()

    if code in COUNTRY_CODE_TO_LOCALE:
        return COUNTRY_CODE_TO_LOCALE[code]

    if slug in COUNTRY_SLUG_TO_LOCALE:
        return COUNTRY_SLUG_TO_LOCALE[slug]

    return "en"
