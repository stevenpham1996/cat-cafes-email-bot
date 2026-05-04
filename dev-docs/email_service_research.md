# Email Service Research & Implementation Guide

## 1. Executive Summary
**Critical Finding:** You **cannot** safely send 2,000+ marketing emails using a personal Gmail account (`@gmail.com`).

*   **Restriction 1 (Quantity):** Personal Gmail accounts have a strict hard limit of **500 emails per rolling 24-hour period**. Exceeding this will lock your account.
*   **Restriction 2 (Deliverability):** As of February 2024, Google and Yahoo implemented strict DMARC policies. If you try to use a third-party tool (like this bot) to send emails saying they are "From" a `@gmail.com` address, they will be rejected or marked as spam.

**The Solution:** You must use a **Transactional Email Service** (like Brevo or Resend) connected to a **custom domain** (e.g., `marketing@catcafenearme.org`).

---

## 2. The "Personal Gmail" Constraints

### A. Daily Sending Limits
*   **Personal Gmail:** 500 emails / day.
*   **Google Workspace (Paid):** 2,000 emails / day (but still requires strict strict spam monitoring).

### B. The DMARC/SPF Problem (Feb 2024 Update)
When you send an email from a script, you are technically "spoofing" the sender.
*   If you set `SENDER_EMAIL=myname@gmail.com` in this bot, the email originates from a server (e.g., AWS, DigitalOcean, or your local ISP) that is *not* Google's official server.
*   Receiving servers (especially Gmail, Outlook, Yahoo) check the "SPF Record" of the sender domain.
*   Since you do not own `gmail.com`, you cannot authorize your script to send on its behalf.
*   **Result:** The email fails authentication and is rejected.

---

## 3. Recommended Email Service Providers (ESP)

For a volume of ~2,000 emails, here are the optimal providers. Note that "Marketing" platforms (Mailchimp) are different from "Transactional" APIs (what this bot uses), though some offer both.

### Option A: Brevo (Formerly Sendinblue) - *Best Free Tier*
*   **Free Tier:** 300 emails/day (Forever).
*   **Cost for 2,000 emails:**
    *   **Free:** If you spread sending over 7 days (300/day).
    *   **Starter Plan (~$25/mo):** 20,000 emails/month (No daily limit).
*   **Pros:** Very easy to set up; allows "Marketing" campaigns via UI if you want to stop using the bot later.
*   **Cons:** Strict daily limit on free tier.

### Option B: Resend - *Best Developer Experience*
*   **Free Tier:** 3,000 emails/month (Limit: 100/day).
*   **Cost for 2,000 emails:**
    *   **Free:** If you spread sending over 20 days (too slow).
    *   **Pro Plan ($20/mo):** 50,000 emails/month (Unlimited daily).
*   **Pros:** Incredible documentation, modern API, high deliverability.
*   **Cons:** Daily limit on free tier is low.

### Option C: SendGrid - *Industry Standard*
*   **Free Tier:** 100 emails/day.
*   **Cost:** ~$20/mo for the "Essentials" plan (up to 50k emails/mo).

### **Recommendation**
If you are willing to spend **~$20-25**, purchase a one-month subscription to **Brevo** or **Resend**. This allows you to send the full batch of 2,000 emails in one or two days without hitting daily limits.

If you strict on **$0 budget**, use **Brevo** and configure the bot to send **250 emails per day** (keeping a buffer) over the course of 8 days.

---

## 4. Optimal Sending Rate & "Warm-Up"

Even with a paid provider, you cannot send 2,000 emails in minute #1. This looks like a spam attack. You must "warm up" your domain reputation.

### Rate Limiting Strategy
*   **Technical Limit:** Most APIs handle 1000s/sec, but you shouldn't use it.
*   **Recommended Script Rate:** **5-10 emails per minute**.
    *   This equals ~300-600 emails per hour.
    *   This "human-like" pace is less likely to trigger aggressive spam filters.

### Warm-Up Schedule (For 2,000 Total)
If your domain is new to sending email, follow this schedule:
1.  **Day 1:** Send 50 emails.
2.  **Day 2:** Send 100 emails.
3.  **Day 3:** Send 200 emails.
4.  **Day 4:** Send 400 emails.
5.  **Day 5+:** Send remaining.

*Note: Since you are using a verified provider (Brevo/Resend), you can be slightly more aggressive (e.g., start at 200/day), but "slow and steady" wins the race.*

---

## 5. Implementation Guide (Brevo Example)

### Step 1: Get Credentials
1.  Sign up at [Brevo.com](https://www.brevo.com/).
2.  **Add your Domain:** Go to Senders & IP > Domains. Add `catcafenearme.org`.
3.  **Verify Domain:** Add the DNS records (TXT) provided by Brevo to your domain host (GoDaddy, Namecheap, etc.). **This is mandatory.**
4.  **Get API Key:** Go to SMTP & API > Generate new SMTP Key.
    *   **Host:** `smtp-relay.brevo.com`
    *   **Port:** `587`
    *   **User:** (Your login email)
    *   **Password:** (The generated key)

### Step 2: Update Environment
Update your `.env` file with the new credentials:

```bash
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xsmtpsib-12345...
SENDER_EMAIL=marketing@catcafenearme.org  <-- Must match verified domain
```

### Step 3: Run the Bot (Batched)
Since you likely want to stay within limits (or warm up), we should update the bot to accept a limit argument (which it already seems to have via `--dry-run` logic, but we might need a real `--limit` flag for production sending).

**Proposed Command:**
```bash
# Run for only 250 emails today
python src/main.py --limit 250
```
*(Note: We need to verify the script supports a production limit, otherwise we should add it.)*
