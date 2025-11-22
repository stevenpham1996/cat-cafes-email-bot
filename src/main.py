import argparse
import time
import os
from dotenv import load_dotenv

from src.db_client import fetch_listings
from src.url_constructor import construct_listing_url
from src.email_sender import send_email
from src.email_logger import log_email_attempt, check_if_email_sent

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Email Marketing Bot")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending emails or writing to DB")
    args = parser.parse_args()

    if args.dry_run:
        print("--- DRY RUN MODE ACTIVATED: No emails will be sent or logged ---")

    print("Starting Email Marketing Bot...")
    
    # 1. Fetch Listings
    print("Fetching listings...")
    listings = fetch_listings()
    print(f"Found {len(listings)} listings with emails.")
    
    emails_sent_count = 0
    errors_count = 0
    skipped_count = 0
    
    for listing in listings:
        listing_id = listing.get("id")
        recipient = listing.get("email")
        title = listing.get("title")
        
        if not recipient:
            continue
            
        print(f"\nProcessing listing: {title} ({listing_id})")
        
        # 2. Duplicate Check
        # In dry-run, we still check to see what WOULD happen, but we don't skip based on it? 
        # Or we do skip to simulate real run? Let's skip to simulate real run.
        if check_if_email_sent(recipient, listing_id):
            print(f"Skipping: Email already sent to {recipient} for listing {listing_id}.")
            skipped_count += 1
            continue
            
        # 3. Construct URL
        url = construct_listing_url(listing)
        if not url:
            print(f"Error: Could not construct URL for listing {listing_id}. Skipping.")
            if not args.dry_run:
                log_email_attempt(
                    recipient=recipient,
                    listing_id=listing_id,
                    description="Marketing Outreach",
                    sender=os.environ.get("SENDER_EMAIL"),
                    status="failed",
                    error_message="Failed to construct URL (missing location data)"
                )
            errors_count += 1
            continue
            
        # Prepend Domain
        domain = os.environ.get("WEBSITE_DOMAIN", "https://hotyogafinder.com")
        full_url = f"{domain}{url}"
        
        # 4. Prepare Email Context
        context = {
            "title": title,
            "url": full_url
        }
        subject = "Partnership Opportunity with Hot Yoga Studios"
        
        # 5. Send Email (or Simulate)
        sender_email = os.environ.get("SENDER_EMAIL")
        
        if args.dry_run:
            print(f"[Dry Run] Would send email to: {recipient}")
            print(f"[Dry Run] Subject: {subject}")
            print(f"[Dry Run] Context: {context}")
            print(f"[Dry Run] Would log attempt to DB.")
            emails_sent_count += 1 # Count as "success" for dry run stats
            continue

        success = send_email(recipient, subject, context)
        
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
    print(f"Sent: {emails_sent_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {errors_count}")

if __name__ == "__main__":
    main()
