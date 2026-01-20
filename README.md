# GA4 Analytics Dashboard

Interactive Streamlit dashboard for visualizing Google Analytics 4 data with real-time metrics, charts, and trend analysis.

## Features

- 📊 **User Metrics**: Total users, active users, session duration
- 💰 **Revenue Analytics**: Total revenue, ad revenue, in-app purchases, ARPU
- 📈 **Interactive Charts**: Daily, weekly, monthly, and yearly views
- 📉 **Trend Analysis**: Mini sparkline charts and moving averages
- 🎨 **Modern UI**: Clean, responsive design with information tooltips

## Quick Start

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your GA4 credentials:
   - Place your `service-account-key.json` in the project root
   - Or create a `config.json` with your settings

3. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

## Deployment

**Deploy to Streamlit Cloud (Free):**

See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md) for detailed deployment instructions.

Quick steps:
1. Push code to GitHub (already done ✅)
2. Sign in to [Streamlit Cloud](https://share.streamlit.io/)
3. Deploy from your GitHub repository
4. Add your GA4 credentials as secrets
5. Your dashboard is live! 🚀

## Requirements

- Python 3.8+
- GA4 Property ID
- Google Cloud Service Account with GA4 Data API access
- See `requirements.txt` for Python dependencies

## Documentation

- [GA4 API Quirks](GA4_QUIRKS.md) - Common issues and solutions
- [Streamlit Deployment Guide](STREAMLIT_DEPLOYMENT.md) - Hosting instructions
