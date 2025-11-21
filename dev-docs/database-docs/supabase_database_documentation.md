# Supabase Database Documentation for Coworking Places Directory

## Table of Contents

1.  [Introduction](#introduction)
2.  [Database Overview](#database-overview)
3.  [Schema Design](#schema-design)
4.  [Table Definitions](#table-definitions)
    -   [countries](#countries)
    -   [states](#states)
    -   [cities](#cities)
    -   [coworking_places](#coworking_places)
    -   [images](#images)
    -   [reviews](#reviews)
    -   [roles](#roles)
    -   [user_profiles](#user_profiles)
    -   [listing_claims](#listing_claims)
    -   [listing_ownership_history](#listing_ownership_history)
    -   [notifications](#notifications)
    -   [user_favorites](#user_favorites)
    -   [faqs](#faqs)
5.  [Authentication and Authorization](#authentication-and-authorization)
    -   [User Authentication](#user-authentication)
    -   [Row Level Security (RLS)](#row-level-security-rls)
    -   [Storage Object Policies](#storage-object-policies)
    -   [Helper Functions](#helper-functions)
6.  [Database Functions & Triggers](#database-functions--triggers)
    -   [User Profile and Avatar Synchronization](#user-profile-and-avatar-synchronization)
    -   [Listing and Claim State Management Engine](#listing-and-claim-state-management-engine)
    -   [Notification Triggers](#notification-triggers)
    -   [Data Consistency and Maintenance](#data-consistency-and-maintenance)
    -   [Auto-Update Thumbnail Trigger](#update_listing_thumbnail-function-and-trigger)
7.  [Data Relationships](#data-relationships)
8.  [Indexing Strategy](#indexing-strategy)
9.  [Data Migration and Import](#data-migration-and-import)
10. [Performance Considerations](#performance-considerations)
11. [Security Considerations](#security-considerations)
12. [Integration with Next.js](#integration-with-nextjs)
13. [Maintenance and Monitoring](#maintenance-and-monitoring)
14. [Future Considerations](#future-considerations)
15. [Storage Bucket Creation](#storage-bucket-creation)

## Introduction

This document provides a comprehensive technical overview of the Supabase database implementation for the Coworking Places Directory website. The database is designed to store and manage information about coworking spaces across the globe, with an initial focus on Vietnam.

The database is hosted on Supabase with the following details:
- **Project ID**: azbctqxuqldfqddyylpe
- **Name**: Coworking Places across the globe
- **Region**: eu-west-2
- **Status**: ACTIVE_HEALTHY
- **Database Version**: PostgreSQL 15.8.1.054

## Database Overview

The database is built on PostgreSQL and leverages Supabase's additional features:
- **Authentication**: Managed by Supabase Auth
- **Row Level Security (RLS)**: For fine-grained access control
- **Auto-generated APIs**: For easy integration with the Next.js frontend
- **Storage**: For managing images and other assets

The database follows a normalized structure with clear relationships between tables, optimized for the directory's read-heavy operations while maintaining data integrity for write operations.

## Schema Design

The database follows these design principles:

### Naming Conventions
- Table names are plural and use snake_case (e.g., `coworking_places`, `user_profiles`)
- Column names use snake_case
- Primary keys are named `id` (except for `user_profiles` which uses `user_id`)
- Foreign keys follow the pattern `table_name_singular_id` (e.g., `state_id`, `country_id`)

### Data Types
- UUIDs for primary keys of main entities
- TEXT for variable-length strings without size constraints
- VARCHAR for strings with size constraints
- NUMERIC for decimal numbers (e.g., latitude, longitude, ratings)
- INTEGER for whole numbers
- BOOLEAN for true/false values
- TIMESTAMP WITH TIME ZONE for date/time values
- JSONB for structured JSON data (e.g., opening hours, services)
- ENUM types for constrained string values:
  - `user_status`: ENUM with values 'active' and 'suspended'
  - `listing_status`: ENUM with values 'pending', 'approved', 'rejected', and 'inactive'

### Timestamps
All tables include `created_at` and `updated_at` columns to track record changes, automatically managed by Supabase/PostgreSQL.

## Table Definitions

### countries

Stores information about countries covered by the directory.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| name | TEXT | NO | Country name (e.g., "Vietnam") |
| code | VARCHAR(2) | NO | ISO 3166-1 alpha-2 code (e.g., "VN", "US") |
| slug | VARCHAR(2) | NO | lowercase replicate of ISO 3166-1 alpha-2 code  (e.g., "vn", "us") |
| latitude | NUMERIC(10,7) | YES | Geographic coordinate for country center |
| longitude | NUMERIC(10,7) | YES | Geographic coordinate for country center |
| image_small | TEXT | YES | URL for a small representative image of the country |
| image_large | TEXT | YES | URL for a large (regular size) representative image of the country |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- `name` is UNIQUE
- `code` is UNIQUE

**Indexes:**
- Index on `code` for faster lookups

**RLS Policies:**
- Public read access is allowed for all records

### states

Stores administrative regions within countries (e.g., Hồ Chí Minh, Đà Nẵng in Vietnam).

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| name | TEXT | NO | State name (e.g., "Hồ Chí Minh") |
| country_id | UUID | NO | Foreign key to countries.id |
| slug | TEXT | NO | URL-friendly version of the name (e.g., "ho-chi-minh") |
| latitude | NUMERIC(10,7) | YES | Geographic coordinate for state center |
| longitude | NUMERIC(10,7) | YES | Geographic coordinate for state center |
| image_small | TEXT | YES | URL for a small representative image of the state |
| image_large | TEXT | YES | URL for a large (regular size) representative image of the state |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- Unique constraint on (country_id, name)
- Unique constraint on (country_id, slug)
- Foreign key constraint on country_id referencing countries.id

**Indexes:**
- Index on `country_id` for faster joins
- Composite index on (country_id, slug) for URL lookups

**RLS Policies:**
- Public read access is allowed for all records

### cities

Stores cities within states.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| name | TEXT | NO | City name (e.g., "Hanoi") |
| state_id | UUID | YES | Foreign key to states.id |
| country_id | UUID | NO | Foreign key to countries.id |
| slug | TEXT | NO | URL-friendly version of the name (e.g., "hanoi") |
| latitude | NUMERIC(10,7) | YES | Geographic coordinate for city center |
| longitude | NUMERIC(10,7) | YES | Geographic coordinate for city center |
| image_small | TEXT | YES | URL for a small representative image of the city |
| image_large | TEXT | YES | URL for a large (regular size) representative image of the city |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- Foreign key constraint on state_id referencing states.id
- Foreign key constraint on country_id referencing countries.id

**Indexes:**
- Index on `state_id` for faster joins
- Index on `country_id` for faster joins
- **Partial Unique Index on `(country_id, state_id, name)`**: Ensures city names are unique within a given state. This allows different states in the same country to have cities with the same name (e.g., Aurora, Colorado and Aurora, Illinois). This index applies only to cities that have a `state_id`.
- **Partial Unique Index on `(country_id, name)`**: Ensures city names are unique within a country for cities that do *not* have a `state_id`. This handles state-less entities.
- **Partial Unique Index on `(country_id, state_id, slug)`**: Ensures city slugs are unique within a given state, which is critical for URL lookups.
- **Partial Unique Index on `(country_id, slug)`**: Ensures city slugs are unique within a country for cities that do *not* have a `state_id`, also used for URL lookups.

**RLS Policies:**
- Public read access is allowed for all records

### coworking_places

Stores the main details for each coworking space listing.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| title | TEXT | NO | Business name (e.g., "CirCO Dong Du") |
| slug | TEXT | NO | URL-friendly version of the title |
| city_id | UUID | NO | Foreign key to cities.id |
| full_address | TEXT | NO | Complete address string |
| street_address | TEXT | YES | Street and number/details |
| zip_code | VARCHAR(20) | YES | Postal code |
| latitude | NUMERIC(10,7) | YES | Geographic coordinate |
| longitude | NUMERIC(10,7) | YES | Geographic coordinate |
| website_url | TEXT | YES | Business website URL |
| phone | VARCHAR(50) | YES | Contact phone number |
| email | TEXT | YES | Contact email |
| average_rating | NUMERIC(3,2) | YES | Average rating value (0-5) |
| review_count | INTEGER | YES | Number of reviews |
| google_maps_url | TEXT | YES | URL to Google Maps listing |
| opening_hours | JSONB | YES | Structured opening hours |
| services | JSONB | YES | Available services (day pass, membership, etc.) |
| amenities | JSONB | YES | Structured JSON data for available amenities (e.g., `{"Good/Fast Internet": true, "Free Coffee/Tea": false}`). |
| additional_benefits | JSONB | YES | Structured JSON data for additional benefits (e.g., `("Pet-Friendly": true, "Childcare": false, "Quiet/Ambient Space": true,`). |
| owner_user_id | UUID | YES | Foreign key to auth.users.id |
| status | listing_status | NO | The current status of the listing (e.g., 'pending', 'approved', 'rejected', 'inactive'). |
| is_featured | BOOLEAN | YES | Whether the listing is featured (default: false) |
| verified_by_owner | BOOLEAN | NO | Whether the listing is verified by a Business User owner (default: false) |
| listing_note | TEXT | YES | Additional notes for the listing (e.g., 'submitted by Admin') |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- Unique constraint on (city_id, slug)
- Foreign key constraint on city_id referencing cities.id
- Foreign key constraint on owner_user_id referencing auth.users.id
- Check constraint on average_rating (between 0 and 5)
- Check constraint on review_count (>= 0)


**Indexes:**
- Index on `city_id` for faster joins
- Index on `slug` for URL lookups
- Index on `owner_user_id` for filtering by owner
- Index on `status` for filtering by status

**RLS Policies:**
1. Admins have full access to all records
2. Supervisors can select, update, and delete all records
3. Active Business Users can manage (select, insert, update, delete) their own listings (suspended users cannot)
4. Public/Anonymous users can only select approved listings (status = 'approved')

### images

Stores image URLs associated with coworking places.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| coworking_place_id | UUID | NO | Foreign key to coworking_places.id |
| image_url | TEXT | NO | URL of the image |
| title | TEXT | YES | Image category/title |
| order | INTEGER | YES | Display order (default: 0) |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- Foreign key constraint on coworking_place_id referencing coworking_places.id with CASCADE delete

**Indexes:**
- Index on `coworking_place_id` for faster lookups

**RLS Policies:**
- Similar to coworking_places, with appropriate access controls

### reviews

Stores user reviews and ratings for coworking places.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| coworking_place_id | UUID | NO | Foreign key to coworking_places.id |
| user_id | UUID | YES | Foreign key to auth.users.id |
| reviewer_name | TEXT | NO | Name of the reviewer |
| profile_picture_url | TEXT | YES | URL for reviewer's profile picture. Sourced from the `user_profiles.avatar_url` at the time of review submission. |
| rating | NUMERIC(2,1) | NO | Rating value (0-5) |
| description | TEXT | YES | Review text |
| review_date | DATE | YES | Date the review was left/scraped |
| is_approved | TEXT    | NO  | Whether the review is approved. Allowed values: 'true', 'false', 'pending' (default: 'pending') |
| rejection_reason        | TEXT                     | YES      | Reason provided if the review is rejected (is_approved = 'false') |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- Foreign key constraint on coworking_place_id referencing coworking_places.id with CASCADE delete
- Foreign key constraint on user_id referencing auth.users.id with SET NULL on delete
- Check constraint on rating (between 0 and 5)

**Indexes:**
- Index on `coworking_place_id` for faster lookups
- Index on `user_id` for filtering by user
- Index on `is_approved` for filtering approved reviews

**RLS Policies:**
1. Admins and Supervisors have full access to all records
2. Active authenticated users can insert new reviews (suspended users cannot)
3. Active business owners can manage reviews for their own places (suspended users cannot)
4. Public/Anonymous users can only select approved reviews (is_approved = true)

### roles

Defines the available user roles in the system.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | INTEGER | NO | Primary key (serial) |
| name | TEXT | NO | Role name (e.g., "Admin", "Supervisor") |

**Constraints:**
- `name` is UNIQUE

**Predefined Roles:**
1. Admin - Full access to all data and functionality
2. Supervisor - Can manage listings and reviews
3. Business User - Can manage their own listings
4. Public User - Basic authenticated user

**RLS Policies:**
- Admins have full access
- Authenticated users have read access

### user_profiles

Stores additional profile information for authenticated users, linked to Supabase Auth.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| user_id | UUID | NO | Primary key, Foreign key to auth.users.id |
| role_id | INTEGER | NO | Foreign key to roles.id (default: 4 - Public User) |
| full_name | TEXT | YES | User's full name |
| avatar_url | TEXT | YES | URL for user's avatar. Automatically synced from `auth.users.raw_user_meta_data` (via `avatar_url` or `picture` keys upon user creation and `raw_user_meta_data` updates). |
| about_me | TEXT | YES | User's bio or description |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |
| supervisor_pending | BOOLEAN | NO | Whether the user is pending supervisor approval (default: false) |
| supervisor_request_letter | TEXT | YES | Stores the text of the letter submitted by a user when requesting the Supervisor role |
| rejection_reason | TEXT | YES | Reason for rejecting a supervisor role request |
| status_reason | TEXT | YES | Reason for user status changes (suspension/reactivation) |
| status | user_status | NO | User's account status ('active' or 'suspended', default: 'active') |

**Constraints:**
- Primary key and foreign key constraint on user_id referencing auth.users.id with CASCADE delete
- Foreign key constraint on role_id referencing roles.id

**Indexes:**
- Index on `role_id` for faster role lookups

**RLS Policies:**
1. Users can view their own profile (regardless of status)
2. Active users can update their own profile (suspended users cannot)
3. Admins have full access to all profiles

### listing_claims

Stores claims and disputes for coworking place ownership.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| coworking_place_id | UUID | NO | Foreign key to coworking_places.id |
| requesting_user_id | UUID | NO | Foreign key to auth.users.id (user requesting ownership) |
| claim_type | TEXT | NO | Type of claim ('claim' or 'dispute') |
| status | TEXT | NO | Status of the claim ('pending', 'approved', 'rejected', 'needs_more_info') |
| claim_reason | TEXT | YES | Reason for the claim or dispute |
| evidence_urls | JSONB | YES | URLs to evidence documents |
| review_note | TEXT | YES | Notes from supervisor/admin reviewing the claim |
| resolved_by_user_id | UUID | YES | Foreign key to auth.users.id (admin/supervisor who resolved) |
| resolved_at | TIMESTAMP WITH TIME ZONE | YES | When the claim was resolved |
| approved_timestamp | TIMESTAMP WITH TIME ZONE | YES | Timestamp when the claim was approved. Used for "Last Approved Wins" logic. |
| system_notes | JSONB | YES | JSON object for storing automated system notes, e.g., auto-rejection reasons. |
| created_at | TIMESTAMP WITH TIME ZONE | YES | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | YES | Record update timestamp |

**Constraints:**
- Foreign key constraint on coworking_place_id referencing coworking_places.id
- Foreign key constraint on requesting_user_id referencing auth.users.id
- Foreign key constraint on resolved_by_user_id referencing auth.users.id
- Check constraint on claim_type (must be 'claim' or 'dispute')
- Check constraint on status (must be 'pending', 'approved', 'rejected', or 'needs_more_info')

**Indexes:**
- Index on `coworking_place_id` for faster lookups
- Index on `requesting_user_id` for filtering by requester
- Index on `status` for filtering by status
- Recommended: Composite index on `(coworking_place_id, status, approved_timestamp)`

**RLS Policies:**
1. Admins have full access to all claims
2. Supervisors can view and update all claims
3. Business Users can view their own claims
4. Active Business Users can insert their own claims (suspended users cannot)

### listing_ownership_history

Stores an audit trail of all ownership changes for a listing.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | UUID | NO | Primary key |
| listing_id | UUID | NO | Foreign key to coworking_places.id |
| previous_owner_id | UUID | YES | The user_id of the previous owner from auth.users. |
| new_owner_id | UUID | YES | The user_id of the new owner from auth.users. |
| last_approved_claim_id | UUID | YES | The specific claim that triggered this ownership change. NULL if ownership was cleared. |
| changed_at | TIMESTAMP WITH TIME ZONE | YES | Timestamp of the ownership change |

**Constraints:**
- Foreign key constraint on `listing_id` referencing `coworking_places.id` with CASCADE delete.
- Foreign key constraint on `last_approved_claim_id` referencing `listing_claims.id` with SET NULL on delete.

**Indexes:**
- Index on `listing_id` for faster lookups.
- Index on `previous_owner_id`.
- Index on `new_owner_id`.

### notifications

Stores user notifications.

| Column                    | Data Type                | Nullable | Description                                                                  |
|---------------------------|--------------------------|----------|------------------------------------------------------------------------------|
| id                        | UUID                     | NO       | Primary key                                                                  |
| user_id                   | UUID                     | NO       | Foreign key to auth.users.id                                                 |
| type                      | TEXT                     | NO       | Type of notification (e.g., 'new_review', 'listing_claim_status')            |
| content                   | JSONB                    | NO       | Structured JSON data for notification details (e.g., message, link, related entity IDs) |
| is_read                   | BOOLEAN                  | NO       | Whether the notification has been read                                       |
| created_at                | TIMESTAMP WITH TIME ZONE | YES      | Record creation timestamp                                                    |
| updated_at                | TIMESTAMP WITH TIME ZONE | YES      | Record update timestamp                                                      |

**Constraints:**
- Foreign key constraint on `user_id` referencing `auth.users.id` with CASCADE delete.

**Indexes:**
- Index on `user_id` for efficient queries.
- Index on `is_read` for efficient queries.

**RLS Policies:**
- Users can view their own notifications.
- Users can update their own notifications (e.g., mark as read).
- Service role can insert notifications.
- Service role can update notifications.
- Service role can delete notifications.

**Triggers:**
- Trigger `update_notifications_updated_at` before UPDATE on `public.notifications` to update the `updated_at` column.

### user_favorites

Stores user-listing relationships for the favorites feature.

| Column                    | Data Type                | Nullable | Description                                                                  |
|---------------------------|--------------------------|----------|------------------------------------------------------------------------------|
| user_id                   | UUID                     | NO       | Primary key, foreign key to auth.users.id                                   |
| coworking_place_id        | UUID                     | NO       | Primary key, foreign key to coworking_places.id                             |
| created_at                | TIMESTAMP WITH TIME ZONE | NO       | Record creation timestamp (default: now())                                  |

**Constraints:**
- Composite primary key on `(user_id, coworking_place_id)` ensures a user can only favorite a specific listing once.
- Foreign key constraint on `user_id` referencing `auth.users.id` with CASCADE delete.
- Foreign key constraint on `coworking_place_id` referencing `coworking_places.id` with CASCADE delete.

**Indexes:**
- Primary key index on `(user_id, coworking_place_id)` for efficient queries.
- Index on `user_id` for efficient user-specific queries.
- Index on `coworking_place_id` for efficient listing-specific queries.

**RLS Policies:**
- **SELECT Policy**: Users can view their own favorites (`auth.uid() = user_id`).
- **INSERT Policy**: Users can add their own favorites (`auth.uid() = user_id`).
- **DELETE Policy**: Users can remove their own favorites (`auth.uid() = user_id`).

**Usage:**
- Used by the favorites feature to track which listings users have favorited.
- Supports the "My Favorites" sorting option in listing pages.
- Powers the "My Favorites" tab in user profiles.
- Enables persistent favorite state across user sessions.

### faqs

Stores frequently asked questions and their answers.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| id | BIGINT | NO | Primary key, auto-increment |
| question | TEXT | NO | The full text of the question |
| answer | TEXT | NO | The full text of the answer |
| slug | TEXT | NO | A URL-friendly version of the question |
| created_at | TIMESTAMPTZ | NO | Record creation timestamp |

**Constraints:**
- `slug` is UNIQUE

**Indexes:**
- Index on `slug` for faster lookups

**RLS Policies:**
- Public read access is allowed for all records

## Authentication and Authorization

### User Authentication

Authentication is handled by Supabase Auth, which provides:
- Email/password authentication
- OAuth providers (Google, etc.)
- JWT-based session management
- Password reset functionality

The `auth.users` table stores the core user data, including:
- User ID (UUID)
- Email
- Hashed password
- User metadata
- Authentication timestamps

### Row Level Security (RLS)

Row Level Security (RLS) is used to enforce access control at the database level. RLS policies define what rows each user can see or modify based on their role and relationship to the data.

Key RLS concepts implemented:
1. **Public Access**: Anonymous users can only view active listings and approved reviews
2. **User-specific Access**: Users can manage their own profiles and content
3. **Role-based Access**: Different capabilities based on user role (Admin, Supervisor, Business User, Public User)
4. **Owner-based Access**: Business owners can manage their own listings and related content
5. **Status-based Access**: Suspended users have limited access compared to active users

#### 5.2.1 Storage Object Policies for listing-images
- **Select Policy:** Public read access for all images
- **Insert Policy:**
  - Admins and Supervisors can upload to any listing
  - Business Users can upload only to their own listings
  - Must be active (not suspended)
- **Update Policy:** Same authorization as insert
- **Delete Policy:** Same authorization as insert

### Helper Functions

Several PostgreSQL functions support the RLS implementation:

#### is_admin()
Checks if the current user has the Admin role.

```sql
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_profiles
    JOIN public.roles ON user_profiles.role_id = roles.id
    WHERE user_profiles.user_id = auth.uid() AND roles.name = 'Admin'
  );
$$;
```

#### is_supervisor()
Checks if the current user has the Supervisor role.

```sql
CREATE OR REPLACE FUNCTION public.is_supervisor()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_profiles
    JOIN public.roles ON user_profiles.role_id = roles.id
    WHERE user_profiles.user_id = auth.uid() AND roles.name = 'Supervisor'
  );
$$;
```

#### is_owner(place_id)
Checks if the current user is the owner of a specific coworking place.

```sql
CREATE OR REPLACE FUNCTION public.is_owner(place_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.coworking_places
    WHERE id = place_id AND owner_user_id = auth.uid()
  );
$$;
```

#### is_user_active()
Checks if the current user's status is 'active'.

```sql
CREATE OR REPLACE FUNCTION public.is_user_active()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_profiles
    WHERE user_id = auth.uid() AND status = 'active'
  );
$$;
```

## Database Functions & Triggers

The database includes several specialized functions and triggers to handle complex operations and ensure data integrity.

### Data Retrieval Functions

#### `get_cities_with_listing_counts()` Function

This function retrieves a list of cities, ordered by the number of approved coworking listings they contain. It is designed to power UI components like the footer's city dropdown, providing a quick way to navigate to the most active cities.

**Key Features:**
- **Top 25 Limit**: Returns only the top 25 cities with the most listings to ensure performance and a clean UI.
- **Handles Complex Relationships**: Correctly aggregates counts for cities, whether they are linked directly to a country or through a state.
- **Performance**: The logic is executed on the database server for maximum efficiency.

**Complete SQL Function:**
```sql
CREATE OR REPLACE FUNCTION get_cities_with_listing_counts()
RETURNS TABLE (
    id UUID,
    name TEXT,
    slug TEXT,
    country_code TEXT,
    state_slug TEXT,
    listing_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.slug,
        COALESCE(cn_state.code, cn_direct.code)::TEXT AS country_code,
        s.slug AS state_slug,
        COUNT(cp.id) AS listing_count
    FROM
        cities c
    JOIN
        coworking_places cp ON c.id = cp.city_id
    LEFT JOIN
        states s ON c.state_id = s.id
    LEFT JOIN
        countries cn_state ON s.country_id = cn_state.id
    LEFT JOIN
        countries cn_direct ON c.country_id = cn_direct.id
    WHERE
        cp.status = 'approved'
    GROUP BY
        c.id, s.id, cn_state.id, cn_direct.id
    ORDER BY
        listing_count DESC
    LIMIT 25;
END;
$$ LANGUAGE plpgsql;
```

### User Profile and Avatar Synchronization

To ensure that all authenticated users have corresponding entries in the `public.user_profiles` table, and that their profile information (including avatar and full name) is kept in sync with their authentication data, the following database functions and triggers are implemented:

#### `handle_new_user()` Function

This function is automatically executed when a new user record is inserted into the `auth.users` table.

**Trigger:** `on_auth_user_created`
  - Event: `AFTER INSERT`
  - Table: `auth.users`
  - Action: `EXECUTE FUNCTION public.handle_new_user()`

**Key Features:**
- Populates the `user_profiles` table with a new record for the new user.
- Sets the `user_id` to `NEW.id`.
- Extracts `full_name` from `NEW.raw_user_meta_data` (checking `'full_name'`, then `'name'`).
- Extracts `avatar_url` from `NEW.raw_user_meta_data` (checking `'avatar_url'`, then `'picture'`).
- Assigns a default `role_id` (typically 'Public User', e.g., 4, as per existing `roles` table data).
- Sets a default `status` (e.g., 'active').

#### `handle_auth_user_avatar_update()` Function

This function is automatically executed when the `raw_user_meta_data` of an existing user record is updated in the `auth.users` table. Its primary purpose is to keep the `user_profiles.avatar_url` and `user_profiles.full_name` synchronized.

**Trigger:** `on_auth_user_raw_meta_data_updated`
  - Event: `AFTER UPDATE`
  - Table: `auth.users`
  - Condition: `OLD.raw_user_meta_data IS DISTINCT FROM NEW.raw_user_meta_data`
  - Action: `EXECUTE FUNCTION public.handle_auth_user_avatar_update()`

### Listing and Claim State Management Engine

A sophisticated, automated system manages listing ownership, status, and claim resolution. This system is orchestrated by a central function, `recalculate_listing_state`, which is called by a trigger on the `listing_claims` table.

#### `recalculate_listing_state(p_listing_id UUID)` Function

This is the core state management engine. It is a `SECURITY DEFINER` function that applies a set of business rules to determine the correct owner and status of a listing based on its associated claims.

**Key Logic:**
1.  **"Last Approved Wins" Rule**: The function identifies the "winning" claim by finding the one with the most recent `approved_timestamp`. This ensures that the latest approved claim always dictates ownership.
2.  **Ownership Transfer**: If a winning claim is found, and the winner's `requesting_user_id` is different from the current `owner_user_id`, the `coworking_places.owner_user_id` is set to the `requesting_user_id` of that claim, and the listing `status` is set to `approved` (unless it's manually set to 'inactive').
3.  **Initial Activation**: If a winning claim is found from the same user but the listing status is `pending`, the listing status is updated to `approved` without changing ownership. This handles the scenario where Admin/Supervisor creates a listing with assigned owner but unchecked immediate approval.
4.  **Competing Claim Auto-Resolution**: When one claim is approved, this function automatically finds all other `pending` claims for the same listing and updates their status to `rejected`. It also adds structured JSONB notes to the `system_notes` column explaining why it was auto-rejected.
5.  **Initial State Preservation**: If no approved claims exist for a listing, the function does nothing, preserving the initially set `owner_user_id`. This is critical for new listings with only pending claims.
6.  **Ownership History**: Whenever the `owner_user_id` of a listing changes OR when a listing is initially activated, the function logs the event in the `listing_ownership_history` table for a complete audit trail.

**Complete SQL Function:**
```sql
CREATE OR REPLACE FUNCTION public.recalculate_listing_state(p_listing_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  winning_claim RECORD;
  current_listing RECORD;
BEGIN
  -- Get the current listing details
  SELECT owner_user_id, status
  INTO current_listing
  FROM coworking_places
  WHERE id = p_listing_id;

  -- Find the winning claim (most recent approved)
  SELECT id, requesting_user_id, status, approved_timestamp
  INTO winning_claim
  FROM listing_claims
  WHERE coworking_place_id = p_listing_id AND status = 'approved'
  ORDER BY approved_timestamp DESC
  LIMIT 1;

  -- Handle three scenarios when a winning claim is found
  IF FOUND THEN
    
    -- SCENARIO 1: Ownership Transfer (existing logic)
    -- If the winning claim is from a different user, transfer ownership
    IF winning_claim.requesting_user_id IS DISTINCT FROM current_listing.owner_user_id THEN
      -- Update the listing owner and status
      UPDATE coworking_places
      SET
        owner_user_id = winning_claim.requesting_user_id,
        status = CASE 
          WHEN current_listing.status = 'inactive'::listing_status THEN 'inactive'::listing_status 
          ELSE 'approved'::listing_status 
        END
      WHERE id = p_listing_id;

      -- Log the ownership change
      INSERT INTO listing_ownership_history (listing_id, previous_owner_id, new_owner_id, last_approved_claim_id, changed_at)
      VALUES (p_listing_id, current_listing.owner_user_id, winning_claim.requesting_user_id, winning_claim.id, NOW());

      -- Automatically reject other pending claims for the same listing
      UPDATE listing_claims
      SET status = 'rejected',
          system_notes = jsonb_build_object(
            'auto_rejection_reason', 'Another claim was approved',
            'approved_claim_id', winning_claim.id,
            'approved_timestamp', winning_claim.approved_timestamp::text,
            'rejection_timestamp', NOW()::text
          )
      WHERE coworking_place_id = p_listing_id AND status = 'pending';

    -- SCENARIO 2: Initial Activation (new logic)
    -- If the winning claim is from the same user but listing is pending, activate it
    ELSIF current_listing.status = 'pending'::listing_status THEN
      -- Activate the pending listing (owner is already correctly assigned)
      UPDATE coworking_places
      SET status = 'approved'::listing_status
      WHERE id = p_listing_id;

      -- Log the activation
      INSERT INTO listing_ownership_history (listing_id, previous_owner_id, new_owner_id, last_approved_claim_id, changed_at)
      VALUES (p_listing_id, current_listing.owner_user_id, current_listing.owner_user_id, winning_claim.id, NOW());

      -- Automatically reject other pending claims for the same listing
      UPDATE listing_claims
      SET status = 'rejected',
          system_notes = jsonb_build_object(
            'auto_rejection_reason', 'Another claim was approved',
            'approved_claim_id', winning_claim.id,
            'approved_timestamp', winning_claim.approved_timestamp::text,
            'rejection_timestamp', NOW()::text
          )
      WHERE coworking_place_id = p_listing_id AND status = 'pending' AND id != winning_claim.id;

    END IF;
    
    -- SCENARIO 3: No Action Required
    -- If winning claim is from same user and listing is already approved/inactive, do nothing
    -- This preserves the existing behavior for already-active listings
    
  END IF;

  -- If no winning claim is found, the function will simply exit, preserving the initial state.

END;
$$;
```

#### `set_approved_timestamp()` Function and Trigger

-   **Function**: `set_approved_timestamp()`
-   **Trigger**: `trigger_set_approved_timestamp` (`BEFORE INSERT OR UPDATE ON listing_claims`)
-   **Purpose**: This trigger automatically sets the `approved_timestamp` column to the current time (`NOW()`) only when a claim's `status` is changed to `approved`. This timestamp is critical for the "Last Approved Wins" logic in the state recalculation function.

#### `trigger_recalculate_listing_state_on_claim_change()` Trigger

-   **Trigger**: `trigger_recalculate_listing_state` (`AFTER INSERT OR UPDATE ON listing_claims`)
-   **Purpose**: This is the primary trigger for the entire state management system. Any time a claim is inserted or its `status` is updated, this trigger calls the `recalculate_listing_state()` function for the relevant listing. This ensures that the listing's ownership and status are always consistent with the state of its claims.

#### `log_ownership_change()` Function

-   **Purpose**: This `SECURITY DEFINER` function is called by `recalculate_listing_state()` to create an audit trail of ownership changes.
-   **Action**: It inserts a new record into the `listing_ownership_history` table, capturing the listing ID, the previous owner, the new owner, and a reference to the specific `listing_claims` record that triggered the change.

### Notification Triggers

#### `create_claim_status_notification()` Function and Trigger

-   **Function**: `create_claim_status_notification()`
-   **Trigger**: `trigger_claim_status_notification` (`AFTER UPDATE OF status ON listing_claims`)
-   **Purpose**: Automatically sends a notification to a user when the status of their claim changes.

#### `create_dispute_notification_for_owner()` Function and Trigger

-   **Function**: `create_dispute_notification_for_owner()`
-   **Trigger**: `trigger_dispute_notification` (`AFTER INSERT ON listing_claims`)
-   **Condition**: Only runs when the new claim's `claim_type` is 'dispute'.
-   **Purpose**: Automatically sends a notification to the current owner of a listing when a new dispute is filed against it.

### Data Consistency and Maintenance

#### `auto_delete_rejected_listings()` Function

-   **Purpose**: This function provides a mechanism for automatically cleaning up listings that remain in a `rejected` state for an extended period.
-   **Logic**: It identifies and deletes listings that have had a `rejected` status for more than 30 days and do not have any associated `approved` claims.
-   **Cascade Deletion**: The function manually performs a cascade delete, removing associated records from `listing_claims`, `images`, `reviews`, and `user_favorites` before deleting the `coworking_places` record itself.
-   **Execution**: This function is intended to be run periodically via a scheduled job (e.g., daily).

#### `validate_claim_on_inactive_listing()` Function and Trigger

-   **Function**: `validate_claim_on_inactive_listing()`
-   **Trigger**: `trigger_validate_claim_on_inactive_listing` (`BEFORE INSERT ON listing_claims`)
-   **Purpose**: Enforces a business rule that prevents users (except Admins) from submitting new claims for listings that are manually set to `inactive`.

#### `update_listing_thumbnail()` Function and Trigger

**Purpose**: Automatically maintains the `thumbnail_url` field in the `coworking_places` table to always reflect the image with the lowest order value.

**Key Features**:
- **Automatic Execution**: Triggers after any `INSERT`, `UPDATE OF "order"`, or `DELETE` operation on the `images` table
- **Smart Selection**: Finds the image with the lowest `order` value, using `created_at` as a tiebreaker for consistent results
- **Null Handling**: Sets `thumbnail_url` to `NULL` if no images exist for the listing
- **Timestamp Update**: Updates the `updated_at` field in `coworking_places` for proper cache invalidation
- **Debug Logging**: Provides `RAISE NOTICE` statements for monitoring thumbnail updates in development

**Use Cases**:
1. **Image Upload**: When a new image is uploaded, it may become the new thumbnail if it has the lowest order
2. **Image Reordering**: When images are reordered, the thumbnail updates to reflect the new first image
3. **Image Deletion**: When the current thumbnail image is deleted, the next image in order becomes the thumbnail
4. **Bulk Operations**: Handles multiple image operations efficiently at the database level

- **File Location**: `cowork-hub-app/app/api/admin/migrations/auto-update-thumbnail-trigger/create_auto_thumbnail_trigger.sql`

#### `check_all_listings_consistency()` Function

-   **Purpose**: A utility function for Admins to audit the integrity of the data.
-   **Action**: It scans all listings and returns a list of potential inconsistencies, such as:
    -   Listings that have an owner but no corresponding approved claim ("Orphaned Owner").
    -   Listings that are `approved` but have no owner ("Missing Owner").

#### `force_reset_listing_state(p_listing_id UUID)` Function

-   **Purpose**: An emergency `SECURITY DEFINER` function for Admins to manually correct a corrupted or inconsistent listing state.
-   **Action**: It resets the specified listing's `status` to `pending` and clears its `owner_user_id`. This provides a safe way to restore a listing to a clean, default state.

## Data Relationships

The database implements the following relationships:

1.  **One-to-Many Relationships:**
    -   One country has many states OR many cities (Two Relationship Patterns)
    -   One state has many cities
    -   One city has many coworking places
    -   One coworking place has many images
    -   One coworking place has many reviews
    -   One coworking place can have many listing claims
    -   One coworking place has many ownership history records
    -   One user can own multiple coworking places
    -   One user can write multiple reviews
    -   One user can submit multiple listing claims
    -   One role can be assigned to many users

2.  **One-to-One Relationships:**
    -   One auth.users record corresponds to one user_profiles record

## Indexing Strategy

The database uses a strategic indexing approach to optimize query performance:

1.  **Primary Keys:** Automatically indexed
2.  **Foreign Keys:** Indexed for faster joins (e.g., state_id, coworking_place_id)
3.  **Filtering Columns:** Indexed for common WHERE clauses (e.g., is_active, is_approved)
4.  **Sorting Columns:** Indexed for ORDER BY operations
5.  **Composite Indexes:** Used for combined conditions (e.g., country_id + slug). A composite index on `(coworking_place_id, status, approved_timestamp)` in the `listing_claims` table is recommended for optimizing the state recalculation logic.

## Data Migration and Import

The initial data import process involves:

1.  **Data Source:** JSON data containing coworking space information
2.  **Data Mapping:**
    -   Parse address fields into respective columns
    -   Handle contact information
    -   Process ratings and reviews
    -   Extract and store images
    -   Convert services to JSONB format
3.  **Slug Generation:** Create URL-friendly slugs from titles
4.  **Geocoding:** Derive latitude/longitude from addresses if missing
5.  **Data Validation:** Ensure data meets constraints and is properly formatted

### Country Coordinates Update

A specific migration was implemented to add geographic coordinates to the countries table:

1.  **Schema Update:** Added `latitude` and `longitude` columns (NUMERIC(10,7)) to the countries table
2.  **Data Enrichment:** Populated these columns with accurate coordinates for each country center
3.  **Implementation:**
    -   `scripts/update_countries_coordinates.sql`: SQL script to add columns and update values
    -   `scripts/update_countries_coordinates.js`: Node.js script to execute the SQL
4.  **Purpose:** Enables map-based features like country-centered map views when no listings are available

## Performance Considerations

The database is optimized for performance in several ways:

1.  **Indexing:** Strategic indexes on frequently queried columns
2.  **Normalization:** Appropriate level of normalization to balance data integrity and query performance
3.  **JSONB:** Efficient storage of semi-structured data (services, opening hours)
4.  **Query Optimization:** Well-designed schema to support efficient joins and filters
5.  **Caching:** Supabase provides caching capabilities for frequently accessed data

## Security Considerations

Security is implemented at multiple levels:

1.  **Authentication:** Secure user authentication via Supabase Auth
2.  **Authorization:** Fine-grained access control via Row Level Security
3.  **Data Validation:** Constraints and checks to ensure data integrity
4.  **SQL Injection Prevention:** Parameterized queries and Supabase's built-in protections
5.  **Secure Functions:** SECURITY DEFINER functions for privileged operations
6.  **Transaction Management:** Atomic operations for critical data updates
7.  **Ownership Verification:** Multiple layers of verification for ownership changes

## Integration with Next.js

The database integrates with the Next.js frontend through:

1.  **Supabase Client:** Client-side access for authenticated users
2.  **Supabase Admin:** Server-side access for privileged operations
3.  **API Routes:** Next.js API routes for secure database operations
4.  **Server Components:** Direct database access from server components
5.  **TypeScript Types:** Generated types for type-safe database access
6.  **Custom Hooks:** React hooks for data fetching and state management
7.  **Cache Management:** Utilities for refreshing and invalidating cached data

## Maintenance and Monitoring

Database maintenance involves:

1.  **Backups:** Automated backups provided by Supabase
2.  **Schema Evolution:** Managed through migrations
3.  **Performance Monitoring:** Track query performance and resource usage
4.  **Data Integrity Checks:** Regular validation of data consistency using the `check_all_listings_consistency()` function.
5.  **User Management:** Monitoring and managing user accounts and roles

## Future Considerations

The database design accommodates future growth and features:

1.  **Geographic Expansion:** Structure supports adding more countries beyond Vietnam
2.  **Scalability:** Design handles growing number of listings and users
3.  **Advanced Search:** Schema supports implementing full-text search
4.  **Geospatial Queries:** Enhanced geospatial features building on the existing latitude/longitude data, potentially using PostGIS for advanced proximity-based searches and map visualizations
5.  **Internationalization:** Possible extension for multi-language content
6.  **Business Features:** Structure for monetization features (featured listings, subscriptions)
7.  **User-Generated Content:** Framework for user submissions and reviews
8.  **Ownership Management:** Robust system for handling listing ownership claims and disputes
9.  **User Profiles:** Enhanced user profile system with additional information and privacy controls
10. **Automated Workflows:** Database functions and triggers for automating common operations

## 15. Storage Bucket Creation

### 15.1 listing-images Bucket
- **Purpose:** Store uploaded listing images
- **Configuration:**
  - Public access enabled
  - 500 KB (512,000 bytes) file size limit
  - Allowed MIME types: image/jpeg, image/png, image/webp, image/gif