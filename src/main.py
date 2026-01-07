import argparse
import time
import os
import datetime
import random
import json
from dotenv import load_dotenv

from src.db_client import fetch_listings, fetch_preview_listings, get_platform_stats
from src.url_constructor import construct_listing_url
from src.email_sender import send_email, render_email_html
from src.email_logger import log_email_attempt, check_if_email_sent
from src.referral_code_generator import get_badge_html_code, get_text_link_html_code

# Load environment variables
load_dotenv()


def setup_dry_run_directory() -> str:
    """Creates a timestamped directory for dry run outputs."""
    path = os.path.join("dry-run", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(path, exist_ok=True)
    return path


def get_target_language(country_code: str) -> str:
    """Maps a country code to a target language code."""
    country_code = country_code.upper() if country_code else ""
    lang_map = {
        "CH": "de",  # Switzerland -> German
        "DE": "de",
        "ES": "es",
        "FR": "fr",
        "NL": "nl",
        "RU": "ru",
        "PT": "pt",
        "JP": "ja",
        "KR": "ko",
        "CN": "cn",
    }
    return lang_map.get(country_code, "en")


def extract_localized_string(data: any, target_lang: str) -> str:
    """Extracts localized text from a string or dictionary with fallback to English."""
    if not data:
        return ""

    # If it's a string, check if it's a serialized JSON object
    if isinstance(data, str) and data.strip().startswith("{"):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, treat it as a plain legacy string
            pass

    # Handle legacy plain strings
    if isinstance(data, str):
        return data

    # Handle dictionary (either original or parsed from JSON string)
    if isinstance(data, dict):
        return data.get(target_lang) or data.get("en") or ""

    return str(data)


def get_template_name(lang: str) -> str:
    """Determines the email template based on language code."""
    return f"catcafe_email_template_{lang}.html"


def setup_session_log(resume_path: str = None) -> tuple[str, set, int]:
    """
    Sets up the session logging.
    1. Creates a new timestamped log file in log/.
    2. If resume_path is provided, reads processed IDs from it (handling both CSV and legacy formats).
    3. Writes the resumed IDs to the new log file with CSV indexing (History Preservation).
    
    Returns:
        tuple: (new_log_path, processed_ids_set, next_index)
    """
    # Ensure log directory exists
    os.makedirs("log", exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    new_log_path = os.path.join("log", f"session_{timestamp}.txt")
    processed_ids = set()
    history_list = [] # Maintain order for re-indexing

    # Load resume data if provided
    if resume_path:
        if os.path.exists(resume_path):
            print(f"Resuming from log: {resume_path}")
            try:
                with open(resume_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Parse line (handles legacy "id" and new "index,id")
                        parts = line.split(',')
                        if len(parts) > 1:
                            # Likely CSV: try to detect if first part is index or header
                            # If header "index", skip
                            if parts[0].lower() == "index":
                                continue
                            lid = parts[-1].strip()
                        else:
                            # Legacy: just the ID
                            lid = line
                        
                        if lid:
                            if lid not in processed_ids:
                                processed_ids.add(lid)
                                history_list.append(lid)
                                
                print(f"Loaded {len(processed_ids)} IDs from resume file.")
            except Exception as e:
                print(f"Error reading resume file: {e}")
        else:
            print(f"Warning: Resume file {resume_path} not found. Starting fresh.")

    # Initialize new log file (with resume data re-indexed)
    next_index = 1
    try:
        with open(new_log_path, "w", encoding="utf-8") as f:
            # Write Header
            f.write("index,listing_id\n")
            
            # Write History
            for lid in history_list:
                f.write(f"{next_index},{lid}\n")
                next_index += 1
                
        print(f"Session log initialized: {new_log_path} (Next Index: {next_index})")
    except Exception as e:
        print(f"Error creating log file: {e}")
        
    return new_log_path, processed_ids, next_index


def main():
    parser = argparse.ArgumentParser(description="Email Marketing Bot")
    parser.add_argument(
        "--dry-run",
        nargs='?',
        const=None,
        type=int,
        default=False,
        metavar='N',
        help="Dry run mode. Generates N HTML emails to dry-run/ directory "
             "(omit N for all)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of emails to send in this run."
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to a log file to resume from (skips IDs listed in the file)."
    )
    args = parser.parse_args()

    # Determine dry run mode and limit
    is_dry_run = args.dry_run is not False
    dry_run_limit = args.dry_run if isinstance(args.dry_run, int) else None
    dry_run_dir = None
    dry_run_count = 0
    
    # Production Limit
    production_limit = args.limit

    # Rate Limit Configuration
    try:
        rate_limit = int(os.environ.get("RATE_LIMIT", 5))
        if rate_limit <= 0:
            print(f"Warning: Invalid RATE_LIMIT {rate_limit}. Using default 5.")
            rate_limit = 5
    except ValueError:
        print("Warning: RATE_LIMIT must be an larger than 0. Using default 5.")
        rate_limit = 5
    
    sleep_interval = 60.0 / rate_limit * 3
    print(f"Rate Limit: {rate_limit} emails/min (Sleep: {sleep_interval:.2f}s)")

    if is_dry_run:
        dry_run_dir = setup_dry_run_directory()
        print("--- DRY RUN MODE ACTIVATED ---")
        print(f"Output directory: {dry_run_dir}")
        if dry_run_limit:
            print(f"Limit: {dry_run_limit} emails")
        else:
            print("Limit: Unlimited")
    elif production_limit:
        print(f"--- PRODUCTION LIMIT: {production_limit} emails ---")

    print("Starting Email Marketing Bot...")

    # Fetch Listings (Bifurcated Logic)
    listings = []
    
    # Session Logging (only relevant for production)
    processed_ids = set()
    session_log_path = None
    current_index = 1

    if is_dry_run:
        # --- DRY RUN PATH ---
        print("--- DRY RUN: Fetching preview batch (fast mode) ---")
        listings = fetch_preview_listings(limit=500)
        total_available = len(listings)
        print(f"Preview fetched: {total_available} listings.")
        
        # Determine target count
        dry_run_limit = dry_run_limit if dry_run_limit else 5
        
        if total_available > 0:
            print(f"Shuffling preview batch to select up to {dry_run_limit} valid listings...")
            random.shuffle(listings)        
    else:
        # --- PRODUCTION PATH ---
        # 1. Setup Session
        session_log_path, processed_ids, current_index = setup_session_log(args.resume)
        
        # 2. Fetch All
        print("Fetching ALL listings (Production Mode)...")
        listings = fetch_listings()
        print(f"Found {len(listings)} total listings.")
        
        # 3. Filter
        if processed_ids:
            listings = [l for l in listings if str(l.get("id")) not in processed_ids]
            print(f"Filtered down to {len(listings)} listings (removed {len(processed_ids)} processed).")

    # Fetch Platform Stats
    if is_dry_run:
        print("--- DRY RUN: Using mock platform stats ---")
        platform_stats = {
            "platform_studios_count": 1857,
            "platform_cities_count": 293,
            "platform_active_users_count": "2033+"
        }
    else:
        print("Fetching platform stats...")
        try:
            platform_stats = get_platform_stats()
            print(f"Stats fetched: {platform_stats}")
        except Exception as e:
            print(f"Error fetching stats: {e}. Using defaults.")
            platform_stats = {
                "platform_studios_count": 1857,
                "platform_cities_count": 293,
                "platform_active_users_count": "2033+"
            }

    emails_sent_count = 0
    errors_count = 0
    skipped_count = 0
    
    # Open log file for appending
    log_file = None
    if session_log_path:
        try:
            log_file = open(session_log_path, "a", encoding="utf-8")
        except Exception as e:
            print(f"CRITICAL: Failed to open session log for appending: {e}")
            print("Aborting to prevent data loss.")
            return

    try:
        for listing in listings:
            # Check dry run limit
            if (is_dry_run and dry_run_limit is not None
                    and dry_run_count >= dry_run_limit):
                print(f"Dry run limit of {dry_run_limit} reached. Stopping.")
                break
                
            # Check Production Limit
            if (not is_dry_run and production_limit is not None 
                    and emails_sent_count >= production_limit):
                print(f"Production limit of {production_limit} reached. Stopping.")
                break

            listing_id = str(listing.get("id"))
            recipient = listing.get("email")
            title = listing.get("title")
            slug = listing.get("slug")

            if not recipient:
                continue

            # Determine Language early for content and template resolution
            country_code = ((listing.get("cities") or {}).get("countries") or {}).get("code")
            target_lang = get_target_language(country_code)

            print(f"\nProcessing listing: {title} ({listing_id})")

            # 2. Duplicate Check (Database level)
            # Only check database history for production runs.
            # Dry runs should generate artifacts regardless of past activity.
            if not is_dry_run and check_if_email_sent(recipient, listing_id):
                print(f"Skipping: Email already sent to {recipient} for listing "
                      f"{listing_id}.")
                skipped_count += 1
                continue

            # 3. Construct URL
            url = construct_listing_url(listing)
            if not url:
                print(f"Error: Could not construct URL for listing {listing_id}. "
                      "Skipping.")
                if not is_dry_run:
                    log_email_attempt(
                        recipient=recipient,
                        listing_id=listing_id,
                        description="Marketing Outreach",
                        sender=os.environ.get("SENDER_EMAIL"),
                        status="failed",
                        error_message=("Failed to construct URL (missing location"
                                       " data)")
                    )
                errors_count += 1
                continue

            # Prepend Domain
            domain = os.environ.get("WEBSITE_DOMAIN", "https://catcafenearme.org")
            full_url = f"{domain}{url}"
            referral_promotion_url = f"https://www.catcafenearme.org/referral-promotion/{listing_id}"

            # 4. Prepare Email Context
            context = {
                "title": title,
                "listing_url": full_url,
                "referral_promotion_url": referral_promotion_url,
                "thumbnail_url": listing.get("thumbnail_url", ""),
                "full_address": listing.get("full_address", ""),
                "average_rating": listing.get("average_rating", 0),
                "review_count": listing.get("review_count", 0),
                "description": extract_localized_string(listing.get("description"), target_lang),
                "cafe_atmosphere": (listing.get("filters") or {}).get("visitor_experience", {}).get("atmosphere", []),
                "badge_html_code": get_badge_html_code(full_url),
                "text_html_code": get_text_link_html_code(full_url)
            }
            # Add platform stats to context
            context.update(platform_stats)

            subject = "Your cat cafe was added for community visibility"

            # 5. Send Email (or Simulate)
            sender_email = os.environ.get("SENDER_EMAIL")

            # Determine Template
            template_name = get_template_name(target_lang)

            if is_dry_run:
                try:
                    html_content = render_email_html(context, template_name)
                    filename = f"{dry_run_count + 1:03d}_{slug}.html"
                    filepath = os.path.join(dry_run_dir, filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"[Dry Run] Saved email to: {filepath}")
                    dry_run_count += 1
                    emails_sent_count += 1
                except Exception as e:
                    print(f"[Dry Run] Error rendering/saving email: {e}")
                    errors_count += 1
                continue

            success = send_email(recipient, subject, context, template_name)

            # 6. Log Result
            status = "sent" if success else "failed"
            error_msg = None if success else "SMTP sending failed"

            log_email_attempt(
                recipient=recipient,
                listing_id=listing_id,
                description="Marketing Outreach",
                sender=sender_email,
                status=status,
                error_message=error_msg
            )

            if success:
                print(f"Email sent successfully to {recipient}.")
                emails_sent_count += 1
                
                # REAL-TIME LOGGING (Critical for Resume/Data Safety)
                if log_file:
                    try:
                        log_file.write(f"{current_index},{listing_id}\n")
                        log_file.flush()
                        os.fsync(log_file.fileno())
                        current_index += 1
                    except Exception as e:
                        print(f"CRITICAL ERROR: Failed to write to log file: {e}")

                # 7. Rate Limit
                time.sleep(sleep_interval)
            else:
                print(f"Failed to send email to {recipient}.")
                errors_count += 1

    except KeyboardInterrupt:
        print("\n\n--- Process Interrupted by User ---")
    finally:
        if log_file:
            log_file.close()

    print("\n--- Job Complete ---")
    if is_dry_run:
        print(f"Dry Run Generated: {emails_sent_count} files in "
              f"{dry_run_dir}")
    else:
        print(f"Sent: {emails_sent_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors: {errors_count}")
        if session_log_path:
            print(f"Session Log: {session_log_path}")


if __name__ == "__main__":
    main()
