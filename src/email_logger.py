from src.db_client import get_supabase_client

def log_email_attempt(recipient: str, listing_id: str, description: str, sender: str, status: str, error_message: str = None):
    """
    Logs the status of an email attempt to the email_tracking table.
    
    Args:
        recipient (str): The email address of the recipient.
        listing_id (str): The UUID of the listing.
        description (str): Description of the email (e.g., "Initial Outreach").
        sender (str): The sender's email address.
        status (str): 'sent' or 'failed'.
        error_message (str, optional): Error message if failed.
    """
    supabase = get_supabase_client()
    
    data = {
        "recipient": recipient,
        "listing_id": listing_id,
        "email_description": description,
        "sender": sender,
        "status": status,
        "error_message": error_message
    }
    
    try:
        supabase.table("email_tracking").insert(data).execute()
    except Exception as e:
        print(f"Failed to log email attempt for {recipient}: {e}")

def check_if_email_sent(recipient: str, listing_id: str) -> bool:
    """
    Checks if an email has already been successfully sent to the recipient for the given listing.
    
    Args:
        recipient (str): The email address.
        listing_id (str): The listing UUID.
        
    Returns:
        bool: True if a 'sent' record exists, False otherwise.
    """
    supabase = get_supabase_client()
    
    try:
        response = supabase.table("email_tracking") \
            .select("id") \
            .eq("recipient", recipient) \
            .eq("listing_id", listing_id) \
            .eq("status", "sent") \
            .execute()
            
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking email status for {recipient}: {e}")
        # If we can't check, assume False to be safe? Or True to be safe (prevent spam)?
        # Let's assume False but log the error, so we might retry. 
        # Ideally, we should stop if DB is down.
        return False
