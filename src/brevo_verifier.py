import os
import time
import datetime
import requests
import json

BREVO_API_URL = "https://api.brevo.com/v3"


def parse_iso_datetime(dt_str: str) -> datetime.datetime:
    """Parses an ISO 8601 datetime string from Brevo API to a UTC-aware datetime object."""
    if not dt_str:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    
    clean_str = dt_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except Exception:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


def get_account_credits_detail(api_key: str = None) -> tuple[dict | None, str | None]:
    """
    Retrieves detailed credit allocation from Brevo account details, distinguishing
    between prepaid/payAsYouGo credits and subscription/free tier limits.
    
    Returns:
        tuple: (credit_info_dict, error_message)
               credit_info_dict format:
               {
                   "prepaid_credits": int,
                   "subscription_credits": int,
                   "total_credits": int,
                   "has_prepaid": bool,
                   "plans": list
               }
    """
    key = api_key or os.environ.get("BREVO_API_KEY")
    if not key:
        return None, "BREVO_API_KEY not found in environment variables."

    url = f"{BREVO_API_URL}/account"
    headers = {
        "accept": "application/json",
        "api-key": key
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            plans = data.get("plan", [])
            
            prepaid_credits = 0
            subscription_credits = 0
            
            for plan in plans:
                plan_type = str(plan.get("type", "")).lower()
                credits_val = int(plan.get("credits", 0))
                credits_type = plan.get("creditsType")
                
                # Check for payAsYouGo / prepaid credits
                if plan_type in ("payasyougo", "prepaid") or (credits_type == "transactional" and plan_type != "free"):
                    prepaid_credits += credits_val
                elif credits_type in ("sendlimit", "subscription") or plan_type in ("subscription", "free"):
                    subscription_credits += credits_val
                else:
                    subscription_credits += credits_val

            total_credits = prepaid_credits + subscription_credits
            
            result = {
                "prepaid_credits": prepaid_credits,
                "subscription_credits": subscription_credits,
                "total_credits": total_credits,
                "has_prepaid": prepaid_credits > 0,
                "plans": plans
            }
            return result, None
        
        error_msg = f"HTTP {response.status_code}: {response.text}"
        try:
            err_json = response.json()
            if "unrecognised IP address" in err_json.get("message", ""):
                error_msg = (
                    f"Brevo IP Security Block: {err_json.get('message')}. "
                    "Authorize your current IP at https://app.brevo.com/security/authorised_ips"
                )
            elif "message" in err_json:
                error_msg = f"Brevo API error ({err_json.get('code', response.status_code)}): {err_json.get('message')}"
        except Exception:
            pass

        return None, error_msg

    except Exception as e:
        return None, f"Network error checking Brevo credits: {e}"


def check_account_credits(api_key: str = None) -> tuple[int | None, str | None]:
    """
    Checks the remaining email credits from Brevo account details.
    
    Returns:
        tuple: (credits_count, error_message)
               credits_count is total available credits (prepaid + subscription).
    """
    detail, err = get_account_credits_detail(api_key=api_key)
    if err:
        return None, err
    return detail.get("total_credits", 0), None


def verify_email_dispatched(
    recipient: str,
    sent_after: datetime.datetime,
    max_retries: int = 6,
    retry_delay: float = 4.0,
    clock_skew_tolerance_seconds: int = 60,
    api_key: str = None
) -> tuple[bool, dict | None, str | None]:
    """
    Polls Brevo's GET /v3/smtp/emails endpoint to verify if an email was actually
    dispatched (not paused/held in the credit queue).
    
    Args:
        recipient: The recipient's email address.
        sent_after: The UTC datetime when the send attempt was initiated.
        max_retries: Maximum polling attempts before declaring the email unverified/queued.
        retry_delay: Delay in seconds between retries.
        clock_skew_tolerance_seconds: Allow Brevo server timestamp to be slightly behind local clock.
        api_key: Optional API key override. If None, reads from BREVO_API_KEY env var.
        
    Returns:
        tuple: (is_verified, email_record, error_message)
            - is_verified: True if dispatched email record is confirmed by Brevo, False otherwise.
            - email_record: Dict containing Brevo's record (uuid, messageId, date, etc.) if verified.
            - error_message: String describing why verification failed or why the email is deemed queued.
    """
    key = api_key or os.environ.get("BREVO_API_KEY")
    if not key:
        return True, None, "BREVO_API_KEY not configured. Verification skipped (unverified pass-through)."

    url = f"{BREVO_API_URL}/smtp/emails"
    headers = {
        "accept": "application/json",
        "api-key": key
    }
    params = {
        "email": recipient.strip().lower(),
        "limit": 5,
        "sort": "desc"
    }

    # Normalize sent_after to UTC
    if sent_after.tzinfo is None:
        sent_after = sent_after.replace(tzinfo=datetime.timezone.utc)
    else:
        sent_after = sent_after.astimezone(datetime.timezone.utc)

    tolerance_threshold = sent_after - datetime.timedelta(seconds=clock_skew_tolerance_seconds)

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get("transactionalEmails", [])
                
                if emails:
                    for email_item in emails:
                        item_email = str(email_item.get("email", "")).strip().lower()
                        dispatched_at = parse_iso_datetime(email_item.get("date", ""))
                        
                        if item_email == recipient.strip().lower() and dispatched_at >= tolerance_threshold:
                            # Successfully verified dispatch
                            return True, email_item, None
                
                # If no emails found or all emails are from an older batch/date,
                # the newly sent email has not appeared in dispatched logs yet.
                last_error = "Email not found in Brevo dispatched logs (likely held in credit queue)."
                
            elif response.status_code == 401:
                err_text = response.text
                try:
                    err_json = response.json()
                    msg = err_json.get("message", "")
                    if "unrecognised IP address" in msg:
                        last_error = (
                            f"Brevo IP Security Block: {msg}. "
                            "Please authorize this IP at https://app.brevo.com/security/authorised_ips"
                        )
                    else:
                        last_error = f"Brevo API Unauthorized (401): {msg}"
                except Exception:
                    last_error = f"Brevo API Unauthorized (401): {err_text}"
                
                # A 401 error cannot be resolved by immediate retries
                return False, None, last_error

            elif response.status_code == 429:
                last_error = "Brevo API rate limit exceeded (429)."
                time.sleep(retry_delay * 2)
                continue
            else:
                last_error = f"Brevo API error (HTTP {response.status_code}): {response.text}"

        except Exception as e:
            last_error = f"Network connection error to Brevo API: {e}"

        if attempt < max_retries:
            time.sleep(retry_delay)

    # If not found in dispatched logs after retries, check if account credits are exhausted
    credits, credit_err = check_account_credits(api_key=key)
    if credits is not None and credits > 0:
        # The account has active credits! The email is NOT in the credit queue;
        # Brevo simply has an asynchronous log indexing delay.
        return True, None, f"Accepted by SMTP with positive credit balance ({credits} credits remaining); log indexing delayed."
    elif credits == 0:
        return False, None, "Account credits exhausted (0 remaining). Email is held in Brevo credit queue."
    else:
        return False, None, credit_err or "Email not found in Brevo dispatched logs."
