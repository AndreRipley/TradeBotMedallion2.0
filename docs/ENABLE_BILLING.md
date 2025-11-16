# Enable Billing Guide

## Quick Steps to Enable Billing

### Step 1: Go to Billing Console
Open this URL in your browser:
```
https://console.cloud.google.com/billing?project=482825357255
```

### Step 2: Link Billing Account
1. Click "Link a billing account"
2. If you don't have one, click "Create billing account"
3. Fill in the form:
   - Account name: "Trading Bot"
   - Country: Your country
   - Add payment method (credit card)
4. Click "Submit and enable billing"

### Step 3: Verify
You should see "Billing account linked" message

### Step 4: Continue Deployment
Return to terminal and run:
```bash
bash deploy_automated.sh
```

## Cost Information

- **Free Credit**: $300 (90 days)
- **Monthly Cost**: ~$0.10-0.50/month
- **Free Tier**: 2 million requests/month
- **Your Usage**: ~1,950 requests/day = ~58,500/month (well within free tier!)

## Set Billing Alerts

1. Go to: https://console.cloud.google.com/billing/budgets
2. Click "Create Budget"
3. Set amount: $5/month
4. Add email alerts
5. Save

This ensures you'll never be surprised by charges.

## Why Billing is Required

Even though Cloud Run has a free tier, Google requires billing to be enabled to:
- Prevent abuse
- Allow services to scale if needed
- Track usage

Your actual costs will be minimal (~$0.10-0.50/month).

