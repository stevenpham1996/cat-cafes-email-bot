# Refactoring Checklist: Brevo Post-Send Dispatch Verification (Method 2) - Cat Cafe Circle

## 1. Environment & Brevo Verifier Module (`src/brevo_verifier.py`)
- [x] **1.1 Implement `src/brevo_verifier.py`**
    - Create `verify_email_dispatched(recipient, sent_after, max_retries, retry_delay, api_key)` querying `GET https://api.brevo.com/v3/smtp/emails`.
    - Implement robust ISO datetime parsing with UTC normalization and clock-skew tolerance (30 seconds).
    - Handle HTTP responses: 200 (check `transactionalEmails`), 401 (detect unrecognized IP address or invalid key), 429 (rate limit backoff), network errors (retries).
    - Implement `check_account_credits(api_key)` querying `GET https://api.brevo.com/v3/account` for credit diagnostics.

## 2. Orchestrator Integration & Fail-Fast Protection (`src/main.py`)
- [x] **2.1 Integrate Post-Send Verification in Main Dispatch Loop**
    - Capture `sent_attempt_time = datetime.datetime.now(datetime.timezone.utc)` right before `send_email()`.
    - If `send_email()` succeeds via SMTP, call `verify_email_dispatched()`.
- [x] **2.2 Implement Conditional Commit & Fail-Fast Mechanics**
    - If verified: commit `status: 'sent'` in `email_tracking`, write `current_index,listing_id` to session log, increment `emails_sent_count`, and sleep remaining rate limit interval.
    - If unverified/queued: log `status: 'queued'` in `email_tracking`, do NOT write to session log, display prominent quota warning, and immediately break/halt the batch loop.
    - Ensure dry-run mode bypasses verification.

## 3. Automated Unit Testing & Edge Case Coverage
- [x] **3.1 Create Comprehensive Unit Tests (`tests/test_brevo_verifier.py`)**
    - Test successful verification (matching email and timestamp).
    - Test failed verification (empty `transactionalEmails` or old email timestamp).
    - Test unrecognized IP / unauthorized error handling (401).
    - Test rate limit handling (429) and network retry logic.
    - Test account credits checking (`check_account_credits`).
- [x] **3.2 Create Orchestrator Integration Tests in `tests/test_brevo_verifier.py`**
    - Test that verified sends write to session log and insert `sent` in `email_tracking`.
    - Test that queued/unverified sends halt the loop and do NOT write to session log.
    - Run full test suite: `uv run python -m unittest discover tests`.

## 4. Documentation & Configuration Updates
- [x] **4.1 Update `.env.example` and `README.md`**
    - Document `BREVO_API_KEY`, IP whitelist security notice, and new execution flow / troubleshooting in `README.md`.
    - Add `BREVO_API_KEY=` placeholder to `.env.example`.
- [x] **4.2 Update Progress Tracking Document (`dev-docs/task-completion-update.txt`)**
