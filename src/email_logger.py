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
