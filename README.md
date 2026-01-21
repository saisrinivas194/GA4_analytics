# GA4 Analytics Dashboard

A comprehensive, interactive dashboard for visualizing Google Analytics 4 (GA4) data with Google Analytics-style charts and optimized API usage.

## Features

### Metrics Dashboard
- **User Metrics**: Total Users, Active Users with trend analysis
- **Revenue Metrics**: Total Revenue, Ad Revenue, In-App Purchase Revenue
- **Performance Metrics**: Session Duration, ARPU (Average Revenue Per User)
- **Period Comparisons**: Compare current period with previous period

### Interactive Charts
- **Google Analytics Style**: Clean zigzag line charts with micro change indicators
- **Separate Charts**: Individual charts for each metric (no comparison clutter)
- **Visual Indicators**: 
  - Green/red stroke segments showing increases/decreases
  - Up/down triangle markers at each data point
  - Median reference lines for context
- **Multiple Time Periods**: View data for 1 month, 3 months, 6 months, 1 year, 2 years, 5 years, or 10 years
- **Auto-Optimized Granularity**: 
  - 1-3 months → Daily aggregation
  - 1 year → Monthly aggregation
  - 5-10 years → Monthly aggregation
  - Reduces API calls by 70%+

### Performance Optimizations
- **Smart Caching**: 3-hour cache duration (configurable)
- **Manual Refresh**: Control when data is fetched
- **Combined API Calls**: All metrics fetched in single requests
- **Reduced Granularity**: Automatic optimization based on time period

### Authentication
- **Streamlit Secrets**: Secure credential storage for Streamlit Cloud
- **File-Based**: Local development with service account JSON file
- **Auto-Detection**: Automatically detects and uses available authentication method

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Google Cloud Project with GA4 Data API enabled
- GA4 Property ID (numeric, not Measurement ID)
- Service Account with Viewer access to GA4 property

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/saisrinivas194/GA4_analytics.git
   cd GA4_analytics
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up authentication**

   **Option A: Local Development (File-based)**
   - Download your service account JSON key from Google Cloud Console
   - Place it in the project directory as `service-account-key.json`
   - Or specify the path in the dashboard sidebar

   **Option B: Streamlit Cloud (Secrets)**
   - Go to Streamlit Cloud → Settings → Secrets
   - Add your service account credentials in TOML format (see `secrets.toml.example`)

4. **Run the dashboard**
   ```bash
   streamlit run dashboard.py
   ```

## Configuration

### Streamlit Secrets Format

For Streamlit Cloud deployment, add this to Settings → Secrets:

```toml
[ga4]
property_id = "YOUR_PROPERTY_ID"
date_range_days = 30

[ga4.service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

Use the `convert_to_toml.py` script to convert your JSON key to TOML format.

## Usage

1. **Enter your GA4 Property ID** in the sidebar
2. **Select date range** (Custom dates or Last N days)
3. **View metrics** in the Summary Metrics section
4. **Explore charts** in the Revenue Trends and Daily Users sections
5. **Switch time periods** using the tabs (1 month, 3 months, 6 months, etc.)
6. **Adjust aggregation** (Daily/Weekly/Monthly) - auto-optimized based on period
7. **Refresh data** manually using the refresh button (3-hour cache)

## Chart Features

### User Charts
- **Total Users**: Blue line with median reference
- **Active Users**: Red line with median reference
- **Scale**: Values displayed in hundreds (×100) for readability
- **Micro Changes**: Green triangles (up), red triangles (down) at each point

### Revenue Charts
- **Total Revenue**: Green line with median reference
- **Ad Revenue**: Blue line with median reference
- **In-App Purchase Revenue**: Purple line with median reference
- **Micro Changes**: Visual indicators showing increases/decreases

### Chart Controls
- **Aggregation**: Daily, Weekly, or Monthly (auto-optimized)
- **Trend Lines**: Moving averages for smooth trend visualization
- **Hover Tooltips**: Detailed information on hover
- **Responsive**: Adapts to container width

## API Optimization

The dashboard implements several optimizations to reduce GA4 API calls:

1. **Caching**: 3-hour cache reduces redundant API calls
2. **Granularity Reduction**: 
   - Short periods (1-3 months) use daily data
   - Long periods (1+ years) use monthly data
   - Reduces API calls by 70%+ for long periods
3. **Combined Metrics**: All revenue metrics fetched in one call
4. **Manual Refresh**: No auto-refresh, user controls when to fetch

## File Structure

```
GA4_analytics/
├── dashboard.py              # Main Streamlit dashboard application
├── ga4_pipeline.py          # GA4 API integration and data fetching
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── secrets.toml.example    # Example Streamlit secrets format
└── convert_to_toml.py      # Helper script to convert JSON to TOML
```

## Requirements

- `streamlit` - Web framework
- `pandas` - Data manipulation
- `plotly` - Interactive charts
- `google-analytics-data` - GA4 Data API client

See `requirements.txt` for complete list.

## Troubleshooting

### "Service account key file not found"
- **Local**: Ensure `service-account-key.json` exists in the project directory
- **Streamlit Cloud**: Configure secrets in Settings → Secrets

### "Either service_account_path or service_account_info must be provided"
- Ensure secrets are properly configured in Streamlit Cloud
- Check that `secrets.ga4.service_account` structure matches the example

### "Property ID must be numeric"
- Use your GA4 Property ID (numeric, e.g., "123456789")
- Do NOT use Measurement ID (G-XXXXXXXXXX format)

### Charts not showing data
- Verify your service account has Viewer access to the GA4 property
- Check that GA4 Data API is enabled in Google Cloud Console
- Ensure date range has data available

## License

This project is provided as-is for analytics visualization purposes.

## Support

For issues or questions, please check:
- GA4 Data API documentation
- Streamlit documentation
- Google Cloud Console for API access
