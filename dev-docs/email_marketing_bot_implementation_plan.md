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
        ```
    - Install dependencies.
- [x] **Configure Environment Variables**
    - Create `.env` file.
    - Add `SUPABASE_URL` and `SUPABASE_KEY`.
    - Add `SENDER_EMAIL` (mock/placeholder).
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
- [ ] **Email Service (`src/email_service.py`)**
    - Implement `send_email_mock(recipient, subject, body)`:
        - Print email details to console (simulating sending).
        - Return `True` (success) or `False` (failure).
- [ ] **Logging Service (`src/logger.py` or inside `db_client.py`)**
    - Implement `log_email_attempt(listing_id, recipient, status, error_message=None)`:
        - Insert record into `email_tracking` table.

## 5. Integration & Verification
- [ ] **Main Script (`src/main.py`)**
    - Import all modules.
    - Implement `main()` function:
        - Call `fetch_listings()`.
        - Loop through listings:
            - Construct URL.
            - Check if email already sent (optional optimization for Phase 1).
            - Construct Email Body (simple text with inserted values).
            - Call `send_email_mock()`.
            - Call `log_email_attempt()`.
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
