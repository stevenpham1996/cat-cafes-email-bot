CREATE TABLE IF NOT EXISTS public.email_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient TEXT NOT NULL,
    listing_id UUID REFERENCES public.coworking_places(id),
    email_description TEXT,
    sender TEXT,
    status TEXT, -- 'sent', 'failed'
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    error_message TEXT
);

-- Index for fast duplicate checking (recipient + listing_id)
CREATE INDEX IF NOT EXISTS idx_email_tracking_recipient_listing ON public.email_tracking(recipient, listing_id);
