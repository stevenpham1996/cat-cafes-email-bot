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
uv run python -m src.main --dry-run
```

**Live Run (Sends real emails):**
```bash
uv run python -m src.main
```

## 3. What to Expect

1.  **Fetching Listings**: The bot will query the database for listings with email addresses.
2.  **Processing**: For each listing, it will:
    -   Check if an email has already been sent (to prevent duplicates).
    -   Construct the unique Listing Detail URL.
    -   Render the email template with the business name and URL.
    -   Send the email via SMTP.
    -   Log the attempt to the `email_tracking` table.
3.  **Rate Limiting**: The bot waits 2 seconds between emails to avoid spam filters.
4.  **Output**: The console will show the progress, including sent emails, skips, and errors.

## 4. Troubleshooting

-   **Authentication Error**: Check your `SUPABASE_URL` and `SUPABASE_KEY`.
-   **SMTP Error**: Ensure your SMTP credentials are correct. If using Gmail, you likely need to generate an "App Password".
-   **ModuleNotFoundError**: Make sure to run the script using `uv run python -m src.main` to correctly resolve the `src` package.
