# Implementation Plan - Email Marketing Bot

## 1. Environment & Database Setup
- [x] **Initialize Project Structure**
    - Create project directory `email-marketing-bot` (if not exists).
    - Create `src` directory for source code.
    - Create `scripts` directory for SQL scripts.
- [x] **Setup Python Environment**
    - Create a virtual environment: `python3 -m venv venv`.
    - Create `requirements.txt` with:
        ```
        supabase
        python-dotenv
        jinja2
        ```
    - Install dependencies.
- [x] **Configure Environment Variables**
    - Create `.env` file.
    - Add `SUPABASE_URL` and `SUPABASE_KEY`.
    - Add `SENDER_EMAIL`.
    - Add SMTP credentials: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`.
- [x] **Create Database Table**
    - Create SQL script `scripts/create_email_tracking_table.sql` with the schema from PRD.
    - Execute the script to create `email_tracking` table in Supabase.

## 2. Data Access Layer
- [x] **Database Client (`src/db_client.py`)**
    - Implement `get_supabase_client()` to return the Supabase client instance.
- [x] **Fetch Listings Logic**
    - Implement `fetch_listings()` function in `src/db_client.py`.
    - Query `coworking_places` and join with `cities`, `states`, `countries`.
    - Select required columns: `id`, `title`, `email`, `slug`, `cities.slug`, `states.slug`, `countries.slug`, `states.country_id`, `cities.country_id`, `cities.state_id`.
    - Filter by `email IS NOT NULL`.

## 3. Business Logic Implementation
- [x] **URL Constructor (`src/url_constructor.py`)**
    - Implement `construct_listing_url(listing_data)` function.
    - Logic:
        - If `cities.state_id` is NOT NULL: `/{country_slug}/{state_slug}/{city_slug}/{listing_slug}`
        - If `cities.state_id` is NULL: `/{country_slug}/{city_slug}/{listing_slug}`.
        - Handle missing slugs gracefully (log warning and skip or return None).

## 4. Email & Logging System
- [x] **Email Templates**
    - Create `templates/` directory.
    - Create `templates/email_template.html` with Jinja2 placeholders (`{{ title }}`, `{{ url }}`).
- [x] **Email Sender (`src/email_sender.py`)**
    - Refactor `send_email` to use `smtplib` and `Jinja2`.
    - Load SMTP config from env.
    - Render template with provided context.
    - Send multipart email (HTML + Plain Text).
- [x] **Email Logger (`src/email_logger.py`)**
    - Implement `log_email_attempt(recipient, listing_id, description, sender, status, error_message)`.
    - Insert record into `email_tracking` table.

## 5. Integration & Verification
- [ ] **Main Script (`src/main.py`)**
    - Import all modules.
    - Import all modules.
    - Implement `main()` function:
        - Call `fetch_listings()`.
        - Loop through listings:
            - **Duplicate Check**: Query `email_tracking` to see if `(recipient, listing_id, status='sent')` exists. Skip if true.
            - Construct URL.
            - Prepare Email Context (Title, URL).
            - Call `send_email()`.
            - Call `log_email_attempt()`.
            - **Rate Limit**: `time.sleep(2)` to be polite.
- [ ] **Dry Run & Verification**
    - Run `main.py`.
    - Verify console output for constructed URLs.
    - Verify `email_tracking` table has new records.

## Relevant Files
- `requirements.txt`
- `.env`
- `src/db_client.py`
- `src/url_constructor.py`
- `src/email_service.py`
- `src/main.py`
- `scripts/create_email_tracking_table.sql`
