# Product Requirement Document (PRD): Email Marketing Bot

## 1. Introduction
This document outlines the requirements and technical specifications for an Email Marketing Bot designed for the Hot Yoga Studios directory. The bot's primary purpose is to automate the process of fetching business listings, constructing unique listing URLs, and sending targeted marketing emails to business owners.

## 2. Core Objectives
-   **Data Retrieval**: Efficiently fetch listing data and related location information from the Supabase database.
-   **Data Processing**: Construct accurate Listing Detail Page URLs based on location hierarchies.
-   **Email Automation**: Send personalized emails to business owners (template implementation pending).
-   **Tracking & Logging**: Maintain a robust log of sent emails to track success rates and prevent duplicate sends.

## 3. Functional Requirements

### 3.1. Data Retrieval
The bot must query the `coworking_places` table and join it with location tables (`cities`, `states`, `countries`) to retrieve the following data:
-   **Listing Details**: `id`, `title`, `email`, `slug` (from `coworking_places`).
-   **Location Details**:
    -   City slug (`cities.slug`)
    -   State slug (`states.slug` - if applicable)
    -   Country slug (`countries.slug`)

**Filtering Criteria**:
-   Listings must have a valid `email` address.
-   (Optional) Listings should be `approved` status (to be confirmed, but safe assumption for marketing).

### 3.2. URL Construction
The Listing Detail Page URL must be constructed dynamically based on the location hierarchy.

**Logic**:
1.  **Scenario A: City belongs to a State** (`cities.state_id` is NOT NULL)
    -   URL Format: `https://[domain]/{country_slug}/{state_slug}/{city_slug}/{listing_slug}`
    -   *Note*: Retrieve `country_slug` via `states.country_id` -> `countries.id`.

2.  **Scenario B: City does not belong to a State** (`cities.state_id` is NULL)
    -   URL Format: `https://[domain]/{country_slug}/{city_slug}/{listing_slug}`
    -   *Note*: Retrieve `country_slug` via `cities.country_id` -> `countries.id`.

### 3.3. Email Sending
-   **Recipient**: The email address from `coworking_places.email`.
-   **Sender**: Configurable sender address (e.g., `marketing@hotyogastudios.com`).
-   **Content**:
    -   Subject: (To be defined)
    -   Body: Eloquent, call-to-action style template.
    -   **Dynamic Insertions**:
        -   Business Title (`coworking_places.title`)
        -   Listing Detail URL (constructed above)
-   *Note*: The actual email template implementation is a follow-up development. This phase focuses on the logic and data preparation.

### 3.4. Logging & Tracking
A new database table `email_tracking` will be created to log every email attempt.

**Table Schema: `email_tracking`**
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK, Default: `gen_random_uuid()` | Unique record ID |
| `recipient` | TEXT | NOT NULL | Business email address |
| `listing_id` | UUID | FK to `coworking_places.id` | Associated listing |
| `email_description` | TEXT | | Purpose of the email (e.g., "Initial Outreach") |
| `sender` | TEXT | | Sender email address |
| `status` | TEXT | | 'sent', 'failed' |
| `sent_at` | TIMESTAMPTZ | Default: `now()` | Timestamp of sending |
| `error_message` | TEXT | | (Optional) Reason for failure |

## 4. Technical Specifications

### 4.1. Technology Stack
-   **Language**: Python 3.12
-   **Database Client**: `supabase-py` (or `psycopg2` if direct connection is preferred, but `supabase-py` is recommended for consistency).
-   **Environment Management**: `python-dotenv` for managing API keys and DB credentials.

### 4.2. Database Interactions
-   **Read**: Perform a join query (or multiple queries if using ORM) to fetch `coworking_places` with their associated `cities`, `states`, and `countries`.
-   **Write**: Insert records into `email_tracking` after each email attempt.

### 4.3. Error Handling
-   Gracefully handle missing location data (e.g., a city missing a slug).
-   Log failures in the `email_tracking` table with an error message.
-   Ensure the script can be re-run without spamming (check `email_tracking` before sending).

## 5. Implementation Plan (Phase 1)
1.  **Setup**: Initialize Python environment and install dependencies.
2.  **Database Migration**: Create the `email_tracking` table.
3.  **Script Development**:
    -   Implement `fetch_listings()`: Query DB for target listings.
    -   Implement `construct_url(listing)`: Logic for URL generation.
    -   Implement `send_email(listing, url)`: Placeholder/Mock function for now.
    -   Implement `log_email_attempt()`: Write to `email_tracking`.
4.  **Testing**: Verify URL construction and logging with sample data.

## 6. Open Questions / Assumptions
-   **Domain Name**: What is the base domain for the URLs? (Assumed placeholder `https://[domain]` for now).
-   **Email Provider**: Which SMTP service or API (e.g., SendGrid, AWS SES) will be used?
-   **Scheduling**: How will this bot be triggered? (Cron job, manual run, etc.?)
