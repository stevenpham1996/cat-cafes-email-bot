# Email Marketing Bot - Walkthrough

This guide explains how to configure and run the Email Marketing Bot.

## 1. Configuration

The bot relies on environment variables defined in the `.env` file. You must populate these with your actual credentials before running the script.

### Database Credentials
-   `SUPABASE_URL`: Your Supabase project URL.
-   `SUPABASE_KEY`: Your Supabase service_role key (required for reading/writing to the DB).

### Email Configuration (SMTP)
-   `SMTP_HOST`: Your SMTP server address (e.g., `smtp.gmail.com`).
-   `SMTP_PORT`: Your SMTP port (e.g., `587` for TLS).
-   `SMTP_USER`: Your SMTP username (usually your email address).
-   `SMTP_PASSWORD`: Your SMTP password (or App Password if using Gmail).
-   `SENDER_EMAIL`: The email address that will appear in the "From" field.

### Other
-   `WEBSITE_DOMAIN`: The base domain for your website (e.g., `https://hotyogafinder.com`). Defaults to `https://hotyogastudios.com` if not set.
-   `RATE_LIMIT`: The number of emails to send per minute (e.g., `30`). Defaults to 30 if not set.


## 2. Running the Bot

The project uses `uv` for dependency management.

### Step 1: Install Dependencies
If you haven't already:
```bash
uv pip install -r requirements.txt
```

### Step 2: Run the Script
Execute the main script using `uv run`.

**Dry Run (Recommended for testing):**
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

# Resume from a previous session log file, sending up to 50 more emails
uv run python -m src.main --resume log/session_YYYYMMDD_HHMMSS.txt --limit 50
```

## 3. What to Expect

1.  **Fetching Listings**: The bot will query the database for listings with email addresses.
2.  **Filtering (if resuming)**: If a `--resume` log file is provided, the bot will skip listings already processed in previous runs.
3.  **Processing**: For each listing, it will:
    -   Check if an email has already been sent (to prevent duplicates at the database level).
    -   Construct the unique Listing Detail URL.
    -   Render the email template with the business name and URL.
    -   Send the email via SMTP.
    -   **Real-time Logging**: After successful sending, the `listing_id` will be immediately written to a timestamped session log file in the `log/` directory. This ensures robust progress tracking even in case of unexpected termination.
    -   Log the attempt to the `email_tracking` table (database level).
4.  **Rate Limiting**: The bot will pause between emails based on the `RATE_LIMIT` environment variable (defaults to 30 emails/minute) to manage sending speed and avoid spam filters.
5.  **Output**: The console will show the progress, including sent emails, skips, and errors. The final session log file path will also be displayed for future `--resume` use.

## 4. Troubleshooting

-   **Authentication Error**: Check your `SUPABASE_URL` and `SUPABASE_KEY`.
-   **SMTP Error**: Ensure your SMTP credentials are correct. If using Gmail, you likely need to generate an "App Password".
-   **ModuleNotFoundError**: Make sure to run the script using `uv run python -m src.main` to correctly resolve the `src` package.
