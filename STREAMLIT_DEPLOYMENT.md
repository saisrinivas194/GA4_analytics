# Deploy to Streamlit Community Cloud

This guide will help you deploy your GA4 Analytics Dashboard to Streamlit Community Cloud (free hosting).

## Prerequisites

1. ✅ Your code is already on GitHub: `https://github.com/saisrinivas194/GA4_analytics`
2. ✅ A Streamlit account (sign up at https://streamlit.io/cloud)

## Step-by-Step Deployment

### 1. Sign in to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click **"Sign in"** and authenticate with your GitHub account
3. Authorize Streamlit to access your GitHub repositories

### 2. Deploy Your App

1. Click **"New app"** button
2. Select your repository: `saisrinivas194/GA4_analytics`
3. Select branch: `main`
4. Main file path: `dashboard.py`
5. Click **"Deploy"**

### 3. Configure Secrets (IMPORTANT!)

After deployment, you need to add your GA4 service account credentials as secrets:

1. In your app dashboard, click **"⋮"** (three dots) → **"Settings"**
2. Go to **"Secrets"** tab
3. Add the following secrets in TOML format:

```toml
[ga4]
property_id = "YOUR_PROPERTY_ID"
date_range_days = 30

[ga4.service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

**Important:** 
- Replace `YOUR_PROPERTY_ID` with your numeric GA4 Property ID
- Copy the `private_key` value from your JSON file **exactly as is** (it already has `\n` in it)
- Copy all other values directly from your `service-account-key.json` file
- The `private_key` in TOML should be the same as in JSON (with `\n` already included)

**How to get these values:**

1. Open your `service-account-key.json` file
2. Copy each value and paste into the TOML format above
3. For `property_id`: Use your numeric GA4 Property ID (found in GA4 Admin → Property Settings)

**For the `private_key` field:**
- Copy the ENTIRE `private_key` value from your JSON file (it's a long string)
- The value already contains `\n` characters - **keep them exactly as they are**
- In TOML, you can use triple quotes `"""` for multi-line strings, OR keep it as a single line
- Example format (single line):
  ```toml
  private_key = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQChjAoFe1F5GbrP\\n...\\n-----END PRIVATE KEY-----\\n"
  ```
- Or use triple quotes (multi-line):
  ```toml
  private_key = """-----BEGIN PRIVATE KEY-----
  MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQChjAoFe1F5GbrP
  ...
  -----END PRIVATE KEY-----
  """
  ```

**Important Notes:**
- Copy ALL fields from your JSON file (including `universe_domain`)
- The `property_id` should be your numeric GA4 Property ID (not Measurement ID like G-XXXXXXXXXX)
- See `secrets.toml.example` for a template

### 4. Verify Deployment

1. After adding secrets, Streamlit will automatically redeploy
2. Wait for the deployment to complete (usually 1-2 minutes)
3. Click **"Open app"** to view your dashboard
4. Your dashboard should now be live and accessible!

## Troubleshooting

### App won't deploy
- Check that `dashboard.py` is in the root directory
- Verify `requirements.txt` exists and has all dependencies
- Check the deployment logs for errors

### Authentication errors
- Verify your secrets are correctly formatted (TOML syntax)
- Ensure the service account has GA4 Data API access enabled
- Check that the Property ID is correct (numeric, not G-XXXXXXXXXX)

### Data not loading
- Verify the service account has viewer access to the GA4 property
- Check that the Property ID matches your GA4 property
- Review the app logs in Streamlit Cloud dashboard

## Your App URL

Once deployed, your app will be available at:
```
https://ga4-analytics-XXXXX.streamlit.app
```

You can share this URL with others!

## Updating Your App

1. Make changes to your code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update dashboard"
   git push origin main
   ```
3. Streamlit Cloud will automatically redeploy (usually within 1-2 minutes)

## Security Notes

- ✅ Never commit `service-account-key.json` to GitHub
- ✅ Always use Streamlit secrets for credentials in production
- ✅ The `.gitignore` file already excludes JSON files
- ✅ Secrets are encrypted and only accessible to your app

