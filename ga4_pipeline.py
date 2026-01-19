"""
GA4 Data API Analytics Pipeline

A production-ready Python pipeline for extracting analytics data from Google Analytics 4
using the GA4 Data API with service account authentication.

Author: Senior Data Engineer
Date: 2024
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunReportResponse,
)
from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError
from google.api_core import exceptions as google_exceptions


class GA4Pipeline:
    """
    Main class for interacting with GA4 Data API.
    
    Handles authentication, querying, and data transformation.
    """
    
    def __init__(
        self,
        property_id: str,
        service_account_path: str,
        date_range_days: int = 30
    ):
        """
        Initialize GA4 Pipeline.
        
        Args:
            property_id: GA4 Property ID (numeric, e.g., "123456789")
            service_account_path: Path to service account JSON key file
            date_range_days: Number of days to query (default: 30)
        """
        self.property_id = property_id
        self.service_account_path = service_account_path
        self.date_range_days = date_range_days
        self.client = None
        
        # Validate inputs
        if not property_id or not property_id.isdigit():
            raise ValueError(
                "Property ID must be a numeric string (e.g., '123456789'). "
                "Do not use Measurement ID (G-XXXXXXXXXX)."
            )
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Service account key file not found: {service_account_path}"
            )
        
        # Initialize client
        self._authenticate()
    
    def _authenticate(self) -> None:
        """
        Authenticate with Google Cloud using service account credentials.
        
        Raises:
            GoogleAuthError: If authentication fails
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )
            
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            
        except GoogleAuthError as e:
            raise GoogleAuthError(
                f"Authentication failed. Please verify your service account key file: {e}"
            )
        except Exception as e:
            raise Exception(f"Unexpected error during authentication: {e}")
    
    def _get_date_range(self, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[str, str]:
        """
        Calculate start and end dates for the query.
        
        Args:
            days: Number of days to look back (default: self.date_range_days)
            start_date: Start date in YYYY-MM-DD format (optional, overrides days)
            end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        
        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        # If custom dates provided, use them
        if start_date and end_date:
            return start_date, end_date
        elif start_date:
            # If only start_date provided, use today as end_date
            return start_date, datetime.now().date().strftime("%Y-%m-%d")
        
        # Otherwise, calculate from days
        if days is None:
            days = self.date_range_days
        
        end_date_obj = datetime.now().date()
        start_date_obj = end_date_obj - timedelta(days=days - 1)  # -1 to include today
        
        return start_date_obj.strftime("%Y-%m-%d"), end_date_obj.strftime("%Y-%m-%d")
    
    def _run_report(
        self,
        metrics: List[str],
        dimensions: Optional[List[str]] = None,
        date_range: Optional[tuple[str, str]] = None,
        max_retries: int = 3
    ) -> RunReportResponse:
        """
        Execute a GA4 Data API report request with retry logic.
        
        Args:
            metrics: List of metric names (e.g., ['totalUsers', 'activeUsers'])
            dimensions: Optional list of dimension names (e.g., ['date'])
            date_range: Optional tuple of (start_date, end_date). If None, uses default.
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            RunReportResponse object from GA4 API
        
        Raises:
            Exception: If API call fails after retries
        """
        if date_range is None:
            date_range = self._get_date_range()
        
        start_date, end_date = date_range
        
        # Build request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric) for metric in metrics],
        )
        
        # Add dimensions if provided
        if dimensions:
            request.dimensions = [Dimension(name=dim) for dim in dimensions]
        
        # Execute with retry logic
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self.client.run_report(request)
                return response
                
            except google_exceptions.ResourceExhausted as e:
                # Rate limit - exponential backoff
                wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                    last_exception = e
                else:
                    raise Exception(
                        f"Rate limit exceeded after {max_retries} attempts. "
                        f"Please reduce query frequency or request quota increase."
                    ) from e
                    
            except google_exceptions.PermissionDenied as e:
                raise Exception(
                    "Permission denied. Please verify:\n"
                    "1. Service account has Viewer access to GA4 property\n"
                    "2. Property ID is correct\n"
                    "3. Service account email is added at Property level (not Account level)"
                ) from e
                
            except google_exceptions.InvalidArgument as e:
                raise Exception(
                    f"Invalid request parameters: {e}\n"
                    "Please check metric and dimension names are correct."
                ) from e
                
            except Exception as e:
                raise Exception(f"Unexpected error during API call: {e}") from e
        
        if last_exception:
            raise last_exception
    
    def _parse_response(
        self,
        response: RunReportResponse,
        include_dimensions: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Parse GA4 API response into a clean list of dictionaries.
        
        Args:
            response: RunReportResponse from GA4 API
            include_dimensions: Whether to include dimension values in output
        
        Returns:
            List of dictionaries with metric values
        """
        results = []
        
        for row in response.rows:
            row_data = {}
            
            # Add dimension values
            if include_dimensions and row.dimension_values:
                for i, dim_value in enumerate(row.dimension_values):
                    dim_name = response.dimension_headers[i].name
                    row_data[dim_name] = dim_value.value
            
            # Add metric values
            for i, metric_value in enumerate(row.metric_values):
                metric_name = response.metric_headers[i].name
                # Convert string values to appropriate types
                value = metric_value.value
                try:
                    # Try to convert to float (for revenue metrics)
                    row_data[metric_name] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    row_data[metric_name] = value if value else 0
            
            results.append(row_data)
        
        return results
    
    def fetch_daily_users(self, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch daily total users and active users over time.
        
        Args:
            days: Number of days to query (default: self.date_range_days)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
        
        Returns:
            List of dictionaries with date, totalUsers, and activeUsers
        """
        date_range = self._get_date_range(days, start_date, end_date)
        
        response = self._run_report(
            metrics=['totalUsers', 'activeUsers', 'averageSessionDuration'],
            dimensions=['date'],
            date_range=date_range
        )
        
        results = self._parse_response(response, include_dimensions=True)
        
        # Transform date format from YYYYMMDD to YYYY-MM-DD
        for row in results:
            if 'date' in row:
                date_str = row['date']
                if len(date_str) == 8:  # YYYYMMDD format
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    row['date'] = formatted_date
        
        return results
    
    def fetch_revenue_metrics_long_period(self, days: int) -> Dict[str, float]:
        """
        Fetch revenue metrics for periods longer than 14 months by making multiple API calls.
        
        Args:
            days: Number of days to query (can exceed 14 months)
        
        Returns:
            Dictionary with revenue metrics
        """
        max_days_per_call = 427  # GA4 limit is ~14 months
        total_revenue = 0.0
        total_ad_revenue = 0.0
        total_purchase_revenue = 0.0
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        current_start = start_date
        current_end = min(current_start + timedelta(days=max_days_per_call - 1), end_date)
        
        while current_start <= end_date:
            if current_start > current_end:
                break
            
            date_range = (current_start.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d"))
            
            try:
                response = self._run_report(
                    metrics=['totalRevenue', 'purchaseRevenue'],
                    dimensions=None,
                    date_range=date_range
                )
                
                results = self._parse_response(response, include_dimensions=False)
                
                if results:
                    total_revenue += float(results[0].get('totalRevenue', 0))
                    purchase_revenue = float(results[0].get('purchaseRevenue', 0))
                    total_purchase_revenue += purchase_revenue
                    total_ad_revenue += max(0.0, float(results[0].get('totalRevenue', 0)) - purchase_revenue)
            except Exception:
                # Continue with other calls if one fails
                pass
            
            # Move to next period
            current_start = current_end + timedelta(days=1)
            current_end = min(current_start + timedelta(days=max_days_per_call - 1), end_date)
        
        return {
            'total_revenue': total_revenue,
            'ad_revenue': total_ad_revenue,
            'in_app_purchase_revenue': total_purchase_revenue
        }
    
    def fetch_revenue_metrics(self, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, float]:
        """
        Fetch total revenue, ad revenue, and in-app purchase revenue.
        
        Note: These metrics return totals for the date range (not daily breakdown).
        For daily breakdown, use fetch_daily_revenue().
        
        Args:
            days: Number of days to query (default: self.date_range_days)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
        
        Returns:
            Dictionary with revenue metrics
        """
        date_range = self._get_date_range(days, start_date, end_date)
        
        # Fetch revenue metrics - adRevenue is not available in GA4 Data API
        # Ad revenue from AdMob is typically included in totalRevenue
        # We'll fetch totalRevenue and purchaseRevenue, and calculate ad revenue as difference
        try:
            response = self._run_report(
                metrics=[
                    'totalRevenue',
                    'purchaseRevenue'  # GA4 uses 'purchaseRevenue' for in-app purchases
                ],
                dimensions=None,  # No dimensions = totals for the period
                date_range=date_range
            )
            
            results = self._parse_response(response, include_dimensions=False)
            
            # Extract values (should be single row)
            if results:
                total_revenue = results[0].get('totalRevenue', 0.0)
                purchase_revenue = results[0].get('purchaseRevenue', 0.0)
                # Ad revenue is typically the difference between total and purchase revenue
                # Note: This is an approximation as other revenue sources may exist
                ad_revenue = max(0.0, total_revenue - purchase_revenue)
                
                return {
                    'total_revenue': total_revenue,
                    'ad_revenue': ad_revenue,
                    'in_app_purchase_revenue': purchase_revenue
                }
            else:
                return {
                    'total_revenue': 0.0,
                    'ad_revenue': 0.0,
                    'in_app_purchase_revenue': 0.0
                }
        except Exception as e:
            # If there's an error, return zeros
            return {
                'total_revenue': 0.0,
                'ad_revenue': 0.0,
                'in_app_purchase_revenue': 0.0
            }
    
    def fetch_daily_revenue(self, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch daily revenue breakdown.
        
        Args:
            days: Number of days to query (default: self.date_range_days)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
        
        Returns:
            List of dictionaries with date and revenue metrics
        """
        date_range = self._get_date_range(days, start_date, end_date)
        
        # Note: adRevenue is not available in GA4 Data API
        response = self._run_report(
            metrics=[
                'totalRevenue',
                'purchaseRevenue'
            ],
            dimensions=['date'],
            date_range=date_range
        )
        
        results = self._parse_response(response, include_dimensions=True)
        
        # Transform date format and calculate ad revenue
        for row in results:
            if 'date' in row:
                date_str = row['date']
                if len(date_str) == 8:
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    row['date'] = formatted_date
            
            # Calculate ad revenue as difference (approximation)
            total_revenue = row.get('totalRevenue', 0.0)
            purchase_revenue = row.get('purchaseRevenue', 0.0)
            row['adRevenue'] = max(0.0, total_revenue - purchase_revenue)
        
        return results
    
    def fetch_previous_period_metrics(self, days: int) -> Dict[str, float]:
        """
        Fetch metrics for the previous period (same duration, before current period).
        
        Args:
            days: Number of days for the period
        
        Returns:
            Dictionary with previous period metrics
        """
        try:
            # Calculate previous period dates
            end_date = datetime.now().date() - timedelta(days=days)
            start_date = end_date - timedelta(days=days - 1)
            
            date_range = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            
            # Fetch previous period users
            response_users = self._run_report(
                metrics=['totalUsers', 'activeUsers'],
                dimensions=None,
                date_range=date_range
            )
            
            users_results = self._parse_response(response_users, include_dimensions=False)
            
            # Fetch previous period revenue
            response_revenue = self._run_report(
                metrics=['totalRevenue', 'purchaseRevenue'],
                dimensions=None,
                date_range=date_range
            )
            
            revenue_results = self._parse_response(response_revenue, include_dimensions=False)
            
            if users_results and revenue_results:
                prev_total_users = users_results[0].get('totalUsers', 0)
                prev_active_users = users_results[0].get('activeUsers', 0)
                prev_total_revenue = revenue_results[0].get('totalRevenue', 0.0)
                prev_purchase_revenue = revenue_results[0].get('purchaseRevenue', 0.0)
                prev_ad_revenue = max(0.0, prev_total_revenue - prev_purchase_revenue)
                
                return {
                    'total_users': float(prev_total_users),
                    'active_users': float(prev_active_users),
                    'total_revenue': float(prev_total_revenue),
                    'ad_revenue': float(prev_ad_revenue),
                    'in_app_purchase_revenue': float(prev_purchase_revenue)
                }
            else:
                return {
                    'total_users': 0.0,
                    'active_users': 0.0,
                    'total_revenue': 0.0,
                    'ad_revenue': 0.0,
                    'in_app_purchase_revenue': 0.0
                }
        except Exception:
            # If previous period fetch fails, return zeros
            return {
                'total_users': 0.0,
                'active_users': 0.0,
                'total_revenue': 0.0,
                'ad_revenue': 0.0,
                'in_app_purchase_revenue': 0.0
            }
    
    def calculate_delta(self, current: float, previous: float) -> Optional[float]:
        """
        Calculate percentage change between current and previous period.
        
        Args:
            current: Current period value
            previous: Previous period value
        
        Returns:
            Percentage change, or None if previous is zero
        """
        if previous == 0:
            return None
        return ((current - previous) / previous) * 100
    
    def fetch_all_metrics(self, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch all required metrics and combine into a single response.
        
        Args:
            days: Number of days to query (default: self.date_range_days)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
        
        Returns:
            Dictionary with all metrics in dashboard-ready format
        """
        start_date_str, end_date_str = self._get_date_range(days, start_date, end_date)
        
        # Calculate days for previous period comparison
        if start_date and end_date:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            period_days = (end_dt - start_dt).days + 1
        else:
            if days is None:
                days = self.date_range_days
            period_days = days
        
        # Fetch current period data
        daily_users = self.fetch_daily_users(days, start_date_str, end_date_str)
        daily_revenue = self.fetch_daily_revenue(days, start_date_str, end_date_str)
        revenue_metrics = self.fetch_revenue_metrics(days, start_date_str, end_date_str)
        
        # Calculate summary statistics
        total_users = sum(row.get('totalUsers', 0) for row in daily_users)
        active_users = sum(row.get('activeUsers', 0) for row in daily_users)
        
        # Calculate average session duration (in seconds, convert to minutes)
        session_durations = [row.get('averageSessionDuration', 0) for row in daily_users if row.get('averageSessionDuration', 0) > 0]
        avg_session_duration_seconds = sum(session_durations) / len(session_durations) if session_durations else 0
        avg_session_duration_minutes = avg_session_duration_seconds / 60.0
        
        # Fetch previous period for comparison
        previous_metrics = self.fetch_previous_period_metrics(period_days)
        
        # Calculate deltas (percentage changes)
        current_total_users = float(total_users)
        current_active_users = float(active_users)
        current_total_revenue = revenue_metrics['total_revenue']
        current_ad_revenue = revenue_metrics['ad_revenue']
        current_in_app_revenue = revenue_metrics['in_app_purchase_revenue']
        
        # Calculate ARPU (Average Revenue Per User)
        arpu = current_total_revenue / current_total_users if current_total_users > 0 else 0.0
        
        # Build response structure
        result = {
            "metadata": {
                "property_id": self.property_id,
                "date_range": {
                    "start_date": start_date_str,
                    "end_date": end_date_str
                },
                "generated_at": datetime.utcnow().isoformat() + "Z"
            },
            "daily_users": daily_users,
            "daily_revenue": daily_revenue,
            "summary": {
                "total_users": int(total_users),
                "active_users": int(active_users),
                "total_revenue": float(current_total_revenue),
                "ad_revenue": float(current_ad_revenue),
                "in_app_purchase_revenue": float(current_in_app_revenue),
                "session_duration_minutes": float(avg_session_duration_minutes),
                "arpu": float(arpu),
                "previous_period": {
                    "total_users": int(previous_metrics['total_users']),
                    "active_users": int(previous_metrics['active_users']),
                    "total_revenue": float(previous_metrics['total_revenue']),
                    "ad_revenue": float(previous_metrics['ad_revenue']),
                    "in_app_purchase_revenue": float(previous_metrics['in_app_purchase_revenue'])
                },
                "deltas": {
                    "total_users": self.calculate_delta(current_total_users, previous_metrics['total_users']),
                    "active_users": self.calculate_delta(current_active_users, previous_metrics['active_users']),
                    "total_revenue": self.calculate_delta(current_total_revenue, previous_metrics['total_revenue']),
                    "ad_revenue": self.calculate_delta(current_ad_revenue, previous_metrics['ad_revenue']),
                    "in_app_purchase_revenue": self.calculate_delta(current_in_app_revenue, previous_metrics['in_app_purchase_revenue'])
                }
            }
        }
        
        return result


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment variables.
    
    Args:
        config_path: Path to config.json file (optional)
    
    Returns:
        Dictionary with configuration values
    """
    config = {}
    
    # Try to load from file
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    elif os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
    
    # Override with environment variables if present
    config['property_id'] = os.getenv('GA4_PROPERTY_ID', config.get('property_id'))
    config['service_account_path'] = os.getenv(
        'GA4_SERVICE_ACCOUNT_PATH',
        config.get('service_account_path', 'service-account-key.json')
    )
    config['date_range_days'] = int(os.getenv(
        'GA4_DATE_RANGE_DAYS',
        config.get('date_range_days', 30)
    ))
    
    return config


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='GA4 Data API Analytics Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ga4_pipeline.py
  python ga4_pipeline.py --config config.json
  python ga4_pipeline.py --output analytics_data.json --days 60
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config.json file (default: ./config.json)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path for JSON results (default: stdout)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        help='Number of days to query (overrides config)'
    )
    
    parser.add_argument(
        '--property-id',
        type=str,
        help='GA4 Property ID (overrides config)'
    )
    
    parser.add_argument(
        '--service-account',
        type=str,
        help='Path to service account JSON key (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command-line arguments
    if args.property_id:
        config['property_id'] = args.property_id
    if args.service_account:
        config['service_account_path'] = args.service_account
    if args.days:
        config['date_range_days'] = args.days
    
    # Validate required configuration
    if not config.get('property_id'):
        print("Error: Property ID is required.", file=sys.stderr)
        print("Set GA4_PROPERTY_ID environment variable or provide --property-id", file=sys.stderr)
        sys.exit(1)
    
    if not config.get('service_account_path'):
        print("Error: Service account path is required.", file=sys.stderr)
        print("Set GA4_SERVICE_ACCOUNT_PATH environment variable or provide --service-account", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize pipeline
        pipeline = GA4Pipeline(
            property_id=config['property_id'],
            service_account_path=config['service_account_path'],
            date_range_days=config['date_range_days']
        )
        
        # Fetch all metrics
        print("Fetching GA4 analytics data...", file=sys.stderr)
        data = pipeline.fetch_all_metrics()
        
        # Output results
        output_json = json.dumps(data, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"Results saved to {args.output}", file=sys.stderr)
        else:
            print(output_json)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

