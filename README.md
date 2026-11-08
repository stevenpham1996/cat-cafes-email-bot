# Email Marketing Bot - Walkthrough

This guide explains how to configure and run the Email Marketing Bot.

## 1. Configuration

The bot relies on environment variables defined in the `.env` file. You must populate these with your actual credentials before running the script.

### Database Credentials
-   `SUPABASE_URL`: Your Supabase project URL.
-   `SUPABASE_SECRET_KEY`: Your Supabase service_role key (required for reading/writing to the DB).

### Email Configuration (SMTP & Brevo API)
-   `SMTP_HOST`: Your SMTP server address (e.g., `smtp-relay.brevo.com`).
-   `SMTP_PORT`: Your SMTP port (e.g., `587` for TLS).
-   `SMTP_USER`: Your SMTP username (usually your email address).
-   `SMTP_PASSWORD`: Your SMTP password or key.
-   `SENDER_EMAIL`: The email address that will appear in the "From" field (e.g., `connect@catcafecircle.com`).
-   `BREVO_API_KEY`: Your Brevo v3 API Key (`xkeysib-...`), retrieved from **Brevo Dashboard > SMTP & API > API Keys**. Required for pre-flight credit checks and post-send dispatch verification.

> [!IMPORTANT]
> **Brevo Server IP Whitelist Notice**  
> Brevo enforces an IP security filter on API calls. If the machine or server running the bot has not been authorized, Brevo API requests will fail with `HTTP 401 Unauthorized: We have detected you are using an unrecognised IP address <IP>`.
> - Check your machine's public IP: `curl -s https://api.ipify.org`
> - Authorize your IP address at: [https://app.brevo.com/security/authorised_ips](https://app.brevo.com/security/authorised_ips)
> - Alternatively, disable IP restrictions under your Brevo Security settings if executing from dynamic IP environments or cloud runners.

### Other
-   `WEBSITE_DOMAIN`: The base domain for your website (e.g., `https://catcafecircle.com`). 
-   `RATE_LIMIT`: The number of emails to send per minute (e.g., `5`). Defaults to 5 if not set.


## 2. Running the Bot

The project uses `uv` for dependency management.

### Step 1: Install Dependencies
If you haven't already:
```bash
uv pip install -r requirements.txt
```

### Step 2: Run the Script
Execute the main script using `uv run`.

#### Campaign 1: Initial Outreach (Dual CTA)
Introduces the directory with both Ownership Claim and 30-Day Free Promotion CTAs.

**Dry Run:**
```bash
# Generate 5 sample emails (saved to dry-run/ directory)
uv run python -m src.main --dry-run 5

# Generate all emails (no sending)
uv run python -m src.main --dry-run
```

**Live Run (Sends real emails):**
```bash
# Send all emails (subject to rate limit)
uv run python -m src.main

# Send a maximum of 100 emails in this run
uv run python -m src.main --limit 100

# Resume from a previous session log file
uv run python -m src.main --resume log/session_initial_YYYYMMDD_HHMMSS.txt --limit 50
```

#### Campaign 2: Follow-up Campaign (`--follow-up`)
Re-engages businesses that received initial outreach but have not yet converted.

```bash
# Smart 2-Stage Routing (Claims unverified listings first, then pursues promotions)
uv run python -m src.main --follow-up all

# Targeted Claim Pursuit (Focuses strictly on ownership verification)
uv run python -m src.main --follow-up claim

# Targeted Promotion Pursuit (Focuses strictly on 30-day free featured spotlight)
uv run python -m src.main --follow-up promotion

# Dry Run testing with 5 emails
uv run python -m src.main --dry-run 5 --follow-up claim
uv run python -m src.main --dry-run 5 --follow-up promotion

# Custom cooldown interval (default: 3 days since last email)
uv run python -m src.main --follow-up claim --interval 5

# Bypass cooling-off interval for staging/testing
uv run python -m src.main --follow-up claim --force

# Custom English subject line (automatically translated into all 13 locales)
uv run python -m src.main --follow-up claim --title "Important update regarding your Cat Cafe Circle listing"
```

## 3. What to Expect

1.  **Fetching Listings**: The bot queries the database for target listings based on the active campaign mode:
    - **Initial Campaign**: Queries approved listings with email where referral promotion is not active.
    - **Follow-up Campaign**: Queries listings that previously received initial outreach, ensures cooling-off interval (`--interval`), excludes owners with pending verification claims (`listing_claims`), and skips exhausted capacity regions for promotions.
2.  **Campaign-Isolated Session Logs**: Session files are prefixed by campaign (`log/session_initial_...`, `log/session_followup_claim_...`, `log/session_followup_promotion_...`) with embedded `# campaign:` headers preventing accidental cross-campaign `--resume`.
3.  **Pre-Flight Credit Telemetry**: When `BREVO_API_KEY` is present, the bot queries `GET /v3/account` to display real-time available credits and verify that sending has not been paused due to quota exhaustion.
4.  **Processing & Post-Send Verification**: For each listing, it will:
    -   Check if an email has already been sent (to prevent duplicates at the database level).
    -   Construct the unique Listing Detail URL across all 3 location patterns (`all-cat-cafes-in-` prefix).
    -   Render the dedicated localized email template for the active pursuit in the listing's native locale.
    -   Submit the message through the SMTP relay.
    -   **Post-Send Dispatch Verification**: Queries `GET /v3/smtp/emails` to verify whether Brevo has officially processed and dispatched the email.
    -   **Conditional State Commit**:
        - **If Dispatched**: Inserts `status: 'sent'` into `email_tracking` with the confirmed Brevo message ID and appends `current_index,listing_id` to the session log file.
        - **If Queued (Quota Exceeded)**: When daily credits are exhausted (e.g. Free Tier 300/day limit), Brevo pauses messages in its internal queue instead of rejecting them. The bot detects this, logs `status: 'queued'`, **does NOT** write the listing ID to the session file, and **immediately halts execution (fail-fast)** to prevent dumping additional listings into Brevo's 72-hour discard buffer.
5.  **Rate Limiting**: Pauses between emails according to `RATE_LIMIT` environment variable (automatically deducting verification elapsed time).
6.  **Output**: Displays console progress, sent counts, skips, errors, and session log paths.

## 4. Troubleshooting

-   **Authentication Error**: Check your `SUPABASE_URL` and `SUPABASE_SECRET_KEY`.
-   **SMTP Error**: Ensure your SMTP credentials are correct. For Brevo, use `smtp-relay.brevo.com` on port 587 with your SMTP master key.
-   **Brevo IP Security Block (401 Unauthorized)**: If you see `Brevo IP Security Block: We have detected you are using an unrecognised IP address <IP>`, navigate to [https://app.brevo.com/security/authorised_ips](https://app.brevo.com/security/authorised_ips) and whitelist the IP printed in the console.
-   **Brevo Dispatch Verification Failed / Email Queued**: If the bot halts with an alert that an email was accepted by SMTP but not confirmed as dispatched, your Brevo account's daily sending limit has likely been exhausted. The bot safely preserves your session log up to the last verified email; you can resume cleanly once credits reset with:
    ```bash
    uv run python -m src.main --follow-up claim --resume log/session_followup_claim_TIMESTAMP.txt
    ```
-   **ModuleNotFoundError**: Make sure to run the script using `uv run python -m src.main` to correctly resolve the `src` package.
