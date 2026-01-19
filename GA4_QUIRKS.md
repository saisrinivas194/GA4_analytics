# GA4 Data API Quirks & Common Pitfalls

## Critical Metric Naming Differences

### Users Metrics
- `totalUsers` - Total number of users (correct metric name)
- `activeUsers` - Active users (correct metric name)
- `users` - Does not exist in GA4, use `totalUsers` instead
- `sessions` - Different calculation in GA4 vs Universal Analytics

### Revenue Metrics
- `totalRevenue` - Total revenue from all sources (correct metric name)
- `adRevenue` - Revenue from ads, requires AdMob integration (correct metric name)
- `purchaseRevenue` - Revenue from purchase events, includes in-app purchases (correct metric name)
- `inAppPurchaseRevenue` - Does not exist as a separate metric, use `purchaseRevenue` instead
- `revenue` - Does not exist, use `totalRevenue` instead

Important note: `purchaseRevenue` is the correct metric for in-app purchase revenue. GA4 doesn't have a separate "in-app purchase" metric, so all purchase events including in-app purchases are tracked under `purchaseRevenue`.

## Date Handling

### Date Format in API Response
- GA4 returns dates as `YYYYMMDD` (string, e.g., `"20240101"`)
- Must convert to `YYYY-MM-DD` for dashboard compatibility
- The pipeline handles this conversion automatically

### Date Range Limitations
- Maximum range: **14 months** (~427 days)
- For longer periods, make multiple API calls
- Always use `startDate` and `endDate` parameters (not `days`)

## Property ID vs Measurement ID

### Property ID (for Data API)
The Property ID is a numeric string like `"123456789"`. You can find it in Admin > Property Settings. This is what you need to use for the Data API.

### Measurement ID (for client-side tracking)
The Measurement ID has the format `G-XXXXXXXXXX` and can be found in Admin > Data Streams. Do not use this for the Data API - it's only for client-side tracking.

## Revenue Event Requirements

### Ad Revenue (`adRevenue`)
- Requires Google AdMob integration
- Must have AdMob linked to GA4 property
- Returns `0` or `null` if not configured

### Purchase Revenue (`purchaseRevenue`)
- Requires `purchase` events with `value` parameter
- Event must include:
  ```json
  {
    "event_name": "purchase",
    "value": 29.99,
    "currency": "USD"
  }
  ```
- Returns `0` if no purchase events are configured

### Total Revenue (`totalRevenue`)
- Sum of all revenue sources
- Includes ad revenue, purchase revenue, and other revenue events
- May be `0` if no revenue events are configured

## Dimension and Metric Compatibility

### Safe Combinations
- `date` dimension works with most metrics
- `date` + `totalUsers` - Works correctly
- `date` + `activeUsers` - Works correctly
- `date` + `totalRevenue` - Works correctly
- `date` + `adRevenue` - Works correctly
- `date` + `purchaseRevenue` - Works correctly

### Not All Dimensions Work Together
- Some dimensions cannot be combined
- Always test dimension combinations before production use
- The pipeline uses only `date` dimension for daily breakdowns

## Service Account Permissions

### Required Role
The Viewer role is the minimum required and is sufficient for Data API access. You don't need to grant Editor or Admin roles, as those provide write access and full access respectively, which aren't necessary for reading data.

### Where to Add
The service account must be added at the Property level, not the Account level. To do this, go to Admin > Property > Property Access Management and add the service account email, which you can find in your JSON key file.

### Common Mistakes
- Adding at Account level instead of Property level (won't work)
- Using wrong email - must use service account email, not your personal email
- Forgetting to add service account after creating it

## API Quotas & Rate Limits

### Default Quotas (per Google Cloud project)
- **25,000 requests per day**
- **1,000,000 tokens per day**
- **10,000 tokens per minute**
- **10 concurrent requests**

### Token Calculation
- Each metric = ~10 tokens
- Each dimension = ~10 tokens
- Each row returned = ~10 tokens
- Example: 3 metrics + 1 dimension + 30 days = ~1,200 tokens

### Best Practices
1. **Cache results** - Don't query same date range multiple times
2. **Batch requests** - Combine metrics in single request
3. **Respect limits** - Implement exponential backoff (included in pipeline)
4. **Monitor usage** - Check Google Cloud Console regularly

## Empty or Zero Results

### Possible Causes
1. **No data in date range** - Check GA4 interface to verify data exists
2. **Events not configured** - Revenue metrics require specific events
3. **Wrong property ID** - Verify you're querying the correct property
4. **Date range too recent** - GA4 data can have 24-48 hour delay
5. **Metric not available** - Some metrics require specific integrations

### How to Debug
1. Check GA4 interface for data in the date range
2. Verify events are configured (Admin > Events)
3. Test with a known date range that has data
4. Check API response for error messages
5. Verify service account has access

## Response Structure

### Row Format
```json
{
  "dimension_values": [
    {"value": "20240101"}
  ],
  "metric_values": [
    {"value": "1250"}
  ]
}
```

### Headers
- `dimension_headers` - List of dimension names
- `metric_headers` - List of metric names
- Use headers to map values to names

### Row Count
- Check `rowCount` in response
- `0` means no data for the query
- May indicate wrong date range or missing events

## Common Error Messages

### "User does not have sufficient permissions"
- Service account not added to GA4 property
- Wrong property ID
- Service account added at wrong level (Account vs Property)

### "API not enabled"
- GA4 Data API not enabled in Google Cloud Console
- Billing not enabled (required for some APIs)

### "Invalid property ID"
- Using Measurement ID instead of Property ID
- Property ID is incorrect
- Property doesn't exist or you don't have access

### "Rate limit exceeded"
- Too many requests in short time
- Need to implement caching
- Request quota increase if needed

## Testing Your Setup

### Quick Test Query
```python
from ga4_pipeline import GA4Pipeline

pipeline = GA4Pipeline(
    property_id="YOUR_PROPERTY_ID",
    service_account_path="service-account-key.json"
)

# Test with small date range
data = pipeline.fetch_daily_users(days=7)
print(f"Fetched {len(data)} days of data")
```

### Verify Metrics
1. Check GA4 interface for expected values
2. Compare API results with GA4 dashboard
3. Note: Small discrepancies are normal due to sampling and processing delays

## Production Considerations

### Caching Strategy
- Cache results for at least 1 hour (GA4 data has processing delay)
- Use Redis or similar for distributed caching
- Cache key: `ga4:{property_id}:{start_date}:{end_date}`

### Error Handling
- Implement retry logic (included in pipeline)
- Log all API errors
- Alert on quota exhaustion
- Fallback to cached data if API fails

### Monitoring
- Track API quota usage
- Monitor error rates
- Alert on authentication failures
- Log response times

### Security
- Never commit service account keys
- Use environment variables or secret management
- Rotate keys periodically
- Use least-privilege principle (Viewer role only)

