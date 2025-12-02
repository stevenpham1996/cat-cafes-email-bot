import argparse
import time
import os
import datetime
from dotenv import load_dotenv

from src.db_client import fetch_listings
from src.url_constructor import construct_listing_url
from src.email_sender import send_email, render_email_html
from src.email_logger import log_email_attempt, check_if_email_sent
from src.referral_code_generator import get_badge_html_code, get_text_link_html_code

# Load environment variables
load_dotenv()


def setup_dry_run_directory() -> str:
    """Creates a timestamped directory for dry run outputs."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("dry-run", timestamp)
    os.makedirs(path, exist_ok=True)
    return path


def get_template_name(country_code: str) -> str:
    """Determines the email template based on country code."""
    country_code = country_code.upper() if country_code else ""
    lang_map = {
        "CH": "de", # Switzerland -> German
        "DE": "de",
        "ES": "es",
        "FR": "fr",
        "NL": "nl",
        "RU": "ru",
    }
    lang = lang_map.get(country_code, "en")
    return f"hotyoga_email_template_{lang}.html"


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
    args = parser.parse_args()

    # Determine dry run mode and limit
    is_dry_run = args.dry_run is not False
    dry_run_limit = args.dry_run if isinstance(args.dry_run, int) else None
    dry_run_dir = None
    dry_run_count = 0

    if is_dry_run:
        dry_run_dir = setup_dry_run_directory()
        print("--- DRY RUN MODE ACTIVATED ---")
        print(f"Output directory: {dry_run_dir}")
        if dry_run_limit:
            print(f"Limit: {dry_run_limit} emails")
        else:
            print("Limit: Unlimited")

    print("Starting Email Marketing Bot...")

    # 1. Fetch Listings
    print("Fetching listings...")
    listings = fetch_listings()
    print(f"Found {len(listings)} listings with emails.")

    emails_sent_count = 0
    errors_count = 0
    skipped_count = 0

    for listing in listings:
        # Check dry run limit
        if (is_dry_run and dry_run_limit is not None
                and dry_run_count >= dry_run_limit):
            print(f"Dry run limit of {dry_run_limit} reached. Stopping.")
            break

        listing_id = listing.get("id")
        recipient = listing.get("email")
        title = listing.get("title")
        slug = listing.get("slug")

        if not recipient:
            continue

        print(f"\nProcessing listing: {title} ({listing_id})")

        # 2. Duplicate Check
        # In dry-run, we check what WOULD happen, and skip to simulate
        # a real run.
        if check_if_email_sent(recipient, listing_id):
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
        domain = os.environ.get("WEBSITE_DOMAIN", "https://hotyogafinder.com")
        full_url = f"{domain}{url}"

        # 4. Prepare Email Context
        context = {
            "title": title,
            "listing_url": full_url,
            "thumbnail_url": listing.get("thumbnail_url", ""),
            "full_address": listing.get("full_address", ""),
            "average_rating": listing.get("average_rating", 0),
            "review_count": listing.get("review_count", 0),
            "description": listing.get("description", ""),
            "primary_yoga_style": listing.get("filters", {}).get("primary_yoga_style", []),
            "badge_html_code": get_badge_html_code(full_url),
            "text_html_code": get_text_link_html_code(full_url)
        }
        subject = "Partnership Opportunity with Hot Yoga Studios"

        # 5. Send Email (or Simulate)
        sender_email = os.environ.get("SENDER_EMAIL")

        # Determine Template
        country_code = listing.get("cities", {}).get("countries", {}).get("code")
        template_name = get_template_name(country_code)

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
            # 7. Rate Limit
            time.sleep(2)
        else:
            print(f"Failed to send email to {recipient}.")
            errors_count += 1

    print("\n--- Job Complete ---")
    if is_dry_run:
        print(f"Dry Run Generated: {emails_sent_count} files in "
              f"{dry_run_dir}")
    else:
        print(f"Sent: {emails_sent_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors: {errors_count}")


if __name__ == "__main__":
    main()
