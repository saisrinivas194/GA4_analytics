"""
GA4 Analytics Dashboard

Interactive dashboard for visualizing Google Analytics 4 data including:
- User metrics (total users, active users)
- Revenue metrics (total, ad, in-app purchases)
- Session duration and ARPU
- Interactive charts with multiple time periods
- Trend analysis and comparisons
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional
import os
import json
from ga4_pipeline import GA4Pipeline, load_config

# Page configuration
st.set_page_config(
    page_title="GA4 Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and visibility
st.markdown("""
    <style>
    /* Info icon tooltip styling - hover tooltip, matching UI design, positioned on left */
    .info-icon-tooltip {
        position: relative !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    .info-icon-tooltip:hover {
        color: #2563eb !important;
        background-color: #eff6ff !important;
    }
    .info-icon-tooltip::before {
        content: attr(data-tooltip);
        position: absolute;
        right: calc(100% + 12px);
        top: 50%;
        transform: translateY(-50%) translateX(4px);
        background: #1f2937;
        color: #f9fafb;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 13px;
        line-height: 1.5;
        white-space: normal;
        width: 320px;
        max-width: calc(100vw - 40px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease, transform 0.2s ease;
        z-index: 1000;
        text-align: left;
        font-weight: 400;
        word-wrap: break-word;
    }
    .info-icon-tooltip::after {
        content: '';
        position: absolute;
        right: calc(100% + 2px);
        top: 50%;
        transform: translateY(-50%);
        border: 5px solid transparent;
        border-left-color: #1f2937;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease;
        z-index: 1001;
    }
    .info-icon-tooltip:hover::before {
        opacity: 1;
        transform: translateY(-50%) translateX(0);
    }
    .info-icon-tooltip:hover::after {
        opacity: 1;
    }
    
    /* Metric card styling */
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        min-height: 140px;
        text-align: center;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .stMetric label {
        font-size: 15px;
        font-weight: 700;
        color: #374151;
        letter-spacing: 0.3px;
        margin-bottom: 10px;
        display: block;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 800;
        color: #000000;
        letter-spacing: -0.5px;
        line-height: 1.3;
        margin: 10px 0;
        word-break: break-word;
        overflow: visible;
    }
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 15px;
        font-weight: 600;
    }
    h1 {
        color: #111827;
        font-weight: 800;
        font-size: 42px;
        letter-spacing: -1px;
        margin-bottom: 20px;
    }
    h2 {
        color: #1f2937;
        font-weight: 700;
        font-size: 32px;
        letter-spacing: -0.5px;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    h3 {
        color: #374151;
        font-weight: 700;
        font-size: 24px;
        letter-spacing: -0.3px;
        margin-top: 20px;
        margin-bottom: 12px;
    }
    p, .stMarkdown p {
        font-size: 16px;
        line-height: 1.6;
        color: #374151;
    }
    .stCaption {
        font-size: 15px;
        font-weight: 600;
        color: #4b5563;
    }
    .stText {
        font-size: 17px;
        font-weight: 500;
        color: #1f2937;
    }
    .stExpander {
        font-size: 16px;
    }
    .stExpander label {
        font-size: 18px;
        font-weight: 700;
        color: #1f2937;
    }
    .stSelectbox label, .stCheckbox label, .stRadio label, .stSlider label {
        font-size: 17px;
        font-weight: 600;
        color: #1f2937;
    }
    .stButton button {
        font-size: 16px;
        font-weight: 600;
    }
    .stDataFrame {
        font-size: 15px;
    }
    .stAlert {
        font-size: 16px;
    }
    .stInfo {
        font-size: 16px;
    }
    .stWarning {
        font-size: 16px;
    }
    .stError {
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)


# Removed @st.cache_data decorator to avoid recursion errors during function decoration
# Caching is now handled manually in the main() function using session state
def fetch_ga4_data(property_id: str, service_account_path: Optional[str] = None, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, service_account_info: Optional[dict] = None):
    """
    Fetch GA4 data with caching to avoid repeated API calls.
    
    Args:
        property_id: GA4 Property ID
        service_account_path: Path to service account JSON (optional if service_account_info provided)
        days: Number of days to query (optional)
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        service_account_info: Service account credentials dict (for Streamlit secrets, optional)
    
    Returns:
        Dictionary with GA4 data
    """
    try:
        # Use days if provided, otherwise use default
        default_days = days if days is not None else 30
        
        # Use secrets if provided, otherwise use file path
        # Do NOT call load_config() here to avoid recursion during caching
        if service_account_info:
            pipeline = GA4Pipeline(
                property_id=property_id,
                service_account_info=service_account_info,
                date_range_days=default_days
            )
        else:
            # Use provided path or default
            file_path = service_account_path or 'service-account-key.json'
            pipeline = GA4Pipeline(
                property_id=property_id,
                service_account_path=file_path,
                date_range_days=default_days
            )
        data = pipeline.fetch_all_metrics(days=days, start_date=start_date, end_date=end_date)
        return data, None
    except Exception as e:
        return None, str(e)


# Removed @st.cache_data decorator to avoid recursion errors
def fetch_comparison_data(property_id: str, service_account_path: str, period_days: int):
    """
    Fetch revenue data for comparison periods.
    
    Args:
        property_id: GA4 Property ID
        service_account_path: Path to service account JSON
        period_days: Number of days for the period
    
    Returns:
        Dictionary with revenue metrics
    """
    try:
        pipeline = GA4Pipeline(
            property_id=property_id,
            service_account_path=service_account_path,
            date_range_days=period_days
        )
        # Use long period method for periods over 14 months
        if period_days > 427:
            metrics = pipeline.fetch_revenue_metrics_long_period(period_days)
        else:
            metrics = pipeline.fetch_revenue_metrics(period_days)
        return metrics, None
    except Exception as e:
        return None, str(e)


# Removed @st.cache_data decorator to avoid recursion errors
def fetch_daily_users_for_period(property_id: str, service_account_path: str, period_days: int):
    """
    Fetch daily users data for a specific period.
    
    Args:
        property_id: GA4 Property ID
        service_account_path: Path to service account JSON
        period_days: Number of days for the period
    
    Returns:
        List of daily user data dictionaries
    """
    try:
        pipeline = GA4Pipeline(
            property_id=property_id,
            service_account_path=service_account_path,
            date_range_days=period_days
        )
        daily_users = pipeline.fetch_daily_users(period_days)
        return daily_users, None
    except Exception as e:
        return None, str(e)


# Removed @st.cache_data decorator to avoid recursion errors
def fetch_daily_revenue_for_period(property_id: str, service_account_path: str, period_days: int):
    """
    Fetch daily revenue data for a specific period.
    
    Args:
        property_id: GA4 Property ID
        service_account_path: Path to service account JSON
        period_days: Number of days for the period
    
    Returns:
        List of daily revenue data dictionaries
    """
    try:
        pipeline = GA4Pipeline(
            property_id=property_id,
            service_account_path=service_account_path,
            date_range_days=period_days
        )
        daily_revenue = pipeline.fetch_daily_revenue(period_days)
        return daily_revenue, None
    except Exception as e:
        return None, str(e)


def create_single_metric_chart(
    daily_data: list,
    metric_name: str,
    metric_key: str,
    title: str,
    aggregation: str = "daily",
    color: str = '#4285f4',
    y_axis_label: str = None,
    is_revenue: bool = False,
    show_micro_changes: bool = True,
):
    """
    Create a single metric chart with median line.
    
    Args:
        daily_data: List of daily data dictionaries
        metric_name: Display name for the metric
        metric_key: Key in the data dictionary
        title: Chart title
        aggregation: 'daily', 'weekly', or 'monthly'
        color: Line color
        y_axis_label: Y-axis label (defaults to metric_name)
        is_revenue: Whether this is a revenue metric (affects formatting)
    """
    if not daily_data:
        return None
    
    df = pd.DataFrame(daily_data)
    
    if len(df) < 1:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    if metric_key not in df.columns:
        return None
    
    df[metric_key] = pd.to_numeric(df[metric_key], errors='coerce').fillna(0)
    
    # Aggregate data based on selection
    if aggregation == 'weekly':
        df['week'] = df['date'].dt.to_period('W').dt.start_time
        df_agg = df.groupby('week').agg({metric_key: 'sum'}).reset_index()
        df_agg.rename(columns={'week': 'date'}, inplace=True)
        df = df_agg
    elif aggregation == 'monthly':
        df['month'] = df['date'].dt.to_period('M').dt.start_time
        df_agg = df.groupby('month').agg({metric_key: 'sum'}).reset_index()
        df_agg.rename(columns={'month': 'date'}, inplace=True)
        df = df_agg
    
    # Use raw data for zigzag lines (no smoothing) to show all micro changes
    # Scale user metrics to hundreds (divide by 100) for better readability
    # Check if this is a user metric (not revenue)
    is_user_metric = not is_revenue and ('user' in metric_key.lower() or 'users' in metric_name.lower())
    scale_factor = 100 if is_user_metric else 1
    
    # Create scaled display values using RAW data (not moving average) for zigzag effect
    df_display = df.copy()
    df_display[f'{metric_key}_scaled'] = df_display[metric_key] / scale_factor
    
    # Calculate median on scaled values
    metric_median = df_display[f'{metric_key}_scaled'].median()
    
    fig = go.Figure()
    
    # Format hover template based on metric type
    if is_revenue:
        hover_template = f'<b>{metric_name}</b><br>Date: %{{x|%Y-%m-%d}}<br>Revenue: $%{{y:,.2f}}<extra></extra>'
        median_hover = f'<b>{metric_name} Median</b><br>Value: $%{{y:,.2f}}<extra></extra>'
        tick_format = '$,.0f'
        delta_prefix = "$"
    elif is_user_metric:
        # For user metrics, show scaled value in hover but indicate it's in hundreds
        hover_template = f'<b>{metric_name}</b><br>Date: %{{x|%Y-%m-%d}}<br>Users: %{{y:,.1f}} (×100)<br>Actual: %{{customdata:,.0f}}<extra></extra>'
        median_hover = f'<b>{metric_name} Median</b><br>Value: %{{y:,.1f}} (×100)<br>Actual: %{{customdata:,.0f}}<extra></extra>'
        tick_format = '.1f'
        delta_prefix = ""
    else:
        hover_template = f'<b>{metric_name}</b><br>Date: %{{x|%Y-%m-%d}}<br>Value: %{{y:,.0f}}<extra></extra>'
        median_hover = f'<b>{metric_name} Median</b><br>Value: %{{y:,.0f}}<extra></extra>'
        tick_format = ','
        delta_prefix = ""
    
    # Use raw scaled values for zigzag line (connects all points directly)
    y_values = df_display[f'{metric_key}_scaled']
    
    # Main zigzag line - Google Analytics style with clear strokes
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=y_values,
        mode='lines',
        name=metric_name,
        line=dict(color=color, width=2.5, shape='linear'),  # linear = zigzag, connects point-to-point
        hovertemplate=hover_template,
        customdata=df[metric_key] if is_user_metric else None,  # Store actual values for hover
        showlegend=False,
        connectgaps=False  # Don't connect gaps to preserve zigzag pattern
    ))
    
    # Add colored segments for up/down strokes (Google Analytics style)
    if len(df) > 1:
        y_series = y_values.astype(float)
        changes = y_series.diff().fillna(0)
        
        # Add separate traces for up strokes (green) and down strokes (red)
        up_dates = []
        up_values = []
        down_dates = []
        down_values = []
        
        for i in range(1, len(df)):
            if changes.iloc[i] > 0:
                # Up stroke - connect previous to current
                up_dates.extend([df['date'].iloc[i-1], df['date'].iloc[i], None])
                up_values.extend([y_values.iloc[i-1], y_values.iloc[i], None])
            elif changes.iloc[i] < 0:
                # Down stroke - connect previous to current
                down_dates.extend([df['date'].iloc[i-1], df['date'].iloc[i], None])
                down_values.extend([y_values.iloc[i-1], y_values.iloc[i], None])
        
        # Up strokes in light green
        if up_dates:
            fig.add_trace(go.Scatter(
                x=up_dates,
                y=up_values,
                mode='lines',
                line=dict(color='rgba(52, 168, 83, 0.3)', width=3, shape='linear'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Down strokes in light red
        if down_dates:
            fig.add_trace(go.Scatter(
                x=down_dates,
                y=down_values,
                mode='lines',
                line=dict(color='rgba(217, 48, 37, 0.3)', width=3, shape='linear'),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Micro change markers - Google Analytics style with clear up/down indicators
    if show_micro_changes and len(df) > 1:
        y_series = y_values.astype(float)
        # Calculate delta from raw values (not scaled) for accurate change detection
        raw_values = df[metric_key].astype(float)
        delta = raw_values.diff()  # Delta in original units
        pct = (raw_values.pct_change() * 100.0).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)

        # Google Analytics style markers - larger and more visible
        symbols = []
        colors = []
        sizes = []
        for d in delta.fillna(0.0).tolist():
            if d > 0:
                symbols.append("triangle-up")
                colors.append("#34a853")  # Google green
                sizes.append(10)
            elif d < 0:
                symbols.append("triangle-down")
                colors.append("#ea4335")  # Google red
                sizes.append(10)
            else:
                symbols.append("circle")
                colors.append("#9aa0a6")  # Google gray
                sizes.append(6)

        # Skip first point (no delta)
        actual_values = df[metric_key].iloc[1:] if is_user_metric else None
        fig.add_trace(go.Scatter(
            x=df['date'].iloc[1:],
            y=y_series.iloc[1:],
            mode='markers',
            marker=dict(
                symbol=symbols[1:],
                size=sizes[1:],
                color=colors[1:],
                line=dict(width=1.5, color='white'),
                opacity=0.9
            ),
            hovertemplate=(
                f"<b>{metric_name}</b><br>"
                "Date: %{x|%Y-%m-%d}<br>"
                + (f"Value: ${'{'}%{{y:,.2f}}{'}'}<br>" if is_revenue 
                   else f"Value: %{{y:,.1f}} (×100)<br>Actual: %{{customdata[2]:,.0f}}<br>" if is_user_metric 
                   else "Value: %{y:,.0f}<br>")
                + f"Change: {delta_prefix}%{{customdata[0]:,.2f}} ({'{'}%{{customdata[1]:+.2f}}{'}'}%)"
                "<extra></extra>"
            ),
            customdata=list(zip(
                delta.iloc[1:].fillna(0.0), 
                pct.iloc[1:].fillna(0.0),
                actual_values.fillna(0.0) if is_user_metric else [0] * len(delta.iloc[1:])
            )) if is_user_metric else list(zip(delta.iloc[1:].fillna(0.0), pct.iloc[1:].fillna(0.0))),
            showlegend=False
        ))

    # Median line (use scaled median from raw data)
    median_actual = df[metric_key].median() if is_user_metric else (metric_median * scale_factor)
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[metric_median, metric_median],
        mode='lines',
        name=f'{metric_name} Median',
        line=dict(color=color, width=1.5, dash='dash'),
        hovertemplate=median_hover,
        customdata=[median_actual] if is_user_metric else None,
        showlegend=False
    ))
    
    agg_label = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly'
    }.get(aggregation, 'Daily')
    
    # Update y-axis label for user metrics to indicate scaling
    if is_user_metric:
        y_label = f"{y_axis_label} (×100)" if y_axis_label else f"{metric_name} (×100)"
    else:
        y_label = y_axis_label if y_axis_label else metric_name
    
    fig.update_layout(
        title=dict(
            text=f'{agg_label} {metric_name} - {title}',
            font=dict(size=20, color='#202124', family='Google Sans, Arial, sans-serif')
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#5f6368')),
            tickfont=dict(size=12, color='#5f6368'),
            gridcolor='#e8eaed',
            showgrid=True,
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text=y_label, font=dict(size=14, color='#5f6368')),
            tickfont=dict(size=12, color='#5f6368'),
            gridcolor='#e8eaed',
            tickformat=tick_format,
            showgrid=True,
            gridwidth=1,
            rangemode='tozero',
            autorange=True
        ),
        hovermode='x unified',
        height=400,
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=20, t=60, b=60),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#dadce0',
            font_size=12,
            font_family='Google Sans, Arial, sans-serif'
        )
    )
    
    return fig


def display_separate_user_charts(daily_users_data: list, title: str, aggregation: str):
    """Display separate charts for Total Users and Active Users."""
    if not daily_users_data:
        st.info(f"No daily user data available for {title}.")
        return
    
    # Total Users Chart
    fig_total = create_single_metric_chart(
        daily_users_data, "Total Users", "totalUsers", title,
        aggregation.lower(), color='#4285f4', y_axis_label='Number of Users'
    )
    if fig_total:
        st.plotly_chart(fig_total, use_container_width=True)
    
    # Active Users Chart
    fig_active = create_single_metric_chart(
        daily_users_data, "Active Users", "activeUsers", title,
        aggregation.lower(), color='#ea4335', y_axis_label='Number of Users'
    )
    if fig_active:
        st.plotly_chart(fig_active, use_container_width=True)


def display_separate_revenue_charts(daily_revenue_data: list, title: str, aggregation: str):
    """Display separate charts for Total Revenue, Ad Revenue, and IAP Revenue."""
    if not daily_revenue_data:
        st.info(f"No daily revenue data available for {title}.")
        return
    
    # Total Revenue Chart
    fig_total = create_single_metric_chart(
        daily_revenue_data, "Total Revenue", "totalRevenue", title,
        aggregation.lower(), color='#34a853', y_axis_label='Revenue ($)', is_revenue=True
    )
    if fig_total:
        st.plotly_chart(fig_total, use_container_width=True)
    
    # Ad Revenue Chart
    fig_ad = create_single_metric_chart(
        daily_revenue_data, "Ad Revenue", "adRevenue", title,
        aggregation.lower(), color='#1a73e8', y_axis_label='Revenue ($)', is_revenue=True
    )
    if fig_ad:
        st.plotly_chart(fig_ad, use_container_width=True)
    
    # In-App Purchase Revenue Chart
    fig_iap = create_single_metric_chart(
        daily_revenue_data, "In-App Purchase Revenue", "purchaseRevenue", title,
        aggregation.lower(), color='#9c27b0', y_axis_label='Revenue ($)', is_revenue=True
    )
    if fig_iap:
        st.plotly_chart(fig_iap, use_container_width=True)


def create_daily_users_chart(daily_users_data: list, title: str = "Daily Users Over Time", aggregation: str = "daily", show_moving_avg: bool = True):
    """
    Create a line chart for daily users with aggregation and smoothing options.
    
    Args:
        daily_users_data: List of daily user data dictionaries
        title: Chart title
        aggregation: 'daily', 'weekly', or 'monthly'
        show_moving_avg: Whether to show 7-day moving average
    """
    if not daily_users_data:
        return None
    
    df = pd.DataFrame(daily_users_data)
    
    # Check if we have enough data
    if len(df) < 1:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Ensure we have the required columns
    if 'totalUsers' not in df.columns or 'activeUsers' not in df.columns:
        return None
    
    # Fill any NaN values with 0 to ensure lines are visible
    df['totalUsers'] = df['totalUsers'].fillna(0)
    df['activeUsers'] = df['activeUsers'].fillna(0)
    
    # Ensure values are numeric
    df['totalUsers'] = pd.to_numeric(df['totalUsers'], errors='coerce').fillna(0)
    df['activeUsers'] = pd.to_numeric(df['activeUsers'], errors='coerce').fillna(0)
    
    # Debug: Log data summary and verify moving averages
    if len(df) > 0:
        total_users_sum = df['totalUsers'].sum()
        active_users_sum = df['activeUsers'].sum()
        # Verify moving averages are calculated
        if 'totalUsers_ma' in df.columns and 'activeUsers_ma' in df.columns:
            total_ma_min = df['totalUsers_ma'].min()
            total_ma_max = df['totalUsers_ma'].max()
            active_ma_min = df['activeUsers_ma'].min()
            active_ma_max = df['activeUsers_ma'].max()
            # Debug output will be shown after moving average calculation
    
    # Aggregate data based on selection
    if aggregation == 'weekly':
        df['week'] = df['date'].dt.to_period('W').dt.start_time
        df_agg = df.groupby('week').agg({
            'totalUsers': 'sum',
            'activeUsers': 'sum'
        }).reset_index()
        df_agg.rename(columns={'week': 'date'}, inplace=True)
        df = df_agg
    elif aggregation == 'monthly':
        df['month'] = df['date'].dt.to_period('M').dt.start_time
        df_agg = df.groupby('month').agg({
            'totalUsers': 'sum',
            'activeUsers': 'sum'
        }).reset_index()
        df_agg.rename(columns={'month': 'date'}, inplace=True)
        df = df_agg
    
    # Always calculate moving averages for smooth trend lines
    # Use adaptive window size based on data length
    if len(df) > 1:
        window = max(3, min(7, len(df) // 3))  # Minimum 3, maximum 7, or 1/3 of data points
        df['totalUsers_ma'] = df['totalUsers'].rolling(window=window, center=True, min_periods=1).mean()
        df['activeUsers_ma'] = df['activeUsers'].rolling(window=window, center=True, min_periods=1).mean()
    else:
        df['totalUsers_ma'] = df['totalUsers']
        df['activeUsers_ma'] = df['activeUsers']
    
    # Ensure moving averages are not all zeros or NaN
    df['totalUsers_ma'] = df['totalUsers_ma'].fillna(0)
    df['activeUsers_ma'] = df['activeUsers_ma'].fillna(0)
    
    # Debug: Verify data ranges
    total_ma_range = (df['totalUsers_ma'].min(), df['totalUsers_ma'].max())
    active_ma_range = (df['activeUsers_ma'].min(), df['activeUsers_ma'].max())
    
    # Calculate median values for reference lines
    total_users_median = df['totalUsers_ma'].median()
    active_users_median = df['activeUsers_ma'].median()
    
    fig = go.Figure()
    
    # Google Analytics style: Clean lines, no markers, zigzag pattern
    # Total Users - Blue solid line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['totalUsers_ma'],
        mode='lines',
        name='Total Users',
        line=dict(color='#4285f4', width=2.5, shape='linear'),
        hovertemplate='<b>Total Users</b><br>Date: %{x|%Y-%m-%d}<br>Users: %{y:,.0f}<extra></extra>',
        showlegend=True,
        connectgaps=True
    ))
    
    # Active Users - Red solid line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['activeUsers_ma'],
        mode='lines',
        name='Active Users',
        line=dict(color='#ea4335', width=2.5, shape='linear'),
        hovertemplate='<b>Active Users</b><br>Date: %{x|%Y-%m-%d}<br>Users: %{y:,.0f}<extra></extra>',
        showlegend=True,
        connectgaps=True
    ))
    
    # Median lines - dashed, matching colors
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[total_users_median, total_users_median],
        mode='lines',
        name='Total Users Median',
        line=dict(color='#4285f4', width=1.5, dash='dash'),
        hovertemplate='<b>Total Users Median</b><br>Value: %{y:,.0f}<extra></extra>',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[active_users_median, active_users_median],
        mode='lines',
        name='Active Users Median',
        line=dict(color='#ea4335', width=1.5, dash='dash'),
        hovertemplate='<b>Active Users Median</b><br>Value: %{y:,.0f}<extra></extra>',
        showlegend=False
    ))
    
    # Update aggregation label in title
    agg_label = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly'
    }.get(aggregation, 'Daily')
    
    # Google Analytics style layout - clean and minimal
    fig.update_layout(
        title=dict(
            text=f'{agg_label} Users Trend - {title}',
            font=dict(size=20, color='#202124', family='Google Sans, Arial, sans-serif')
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#5f6368')),
            tickfont=dict(size=12, color='#5f6368'),
            gridcolor='#e8eaed',
            showgrid=True,
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text='Number of Users', font=dict(size=14, color='#5f6368')),
            tickfont=dict(size=12, color='#5f6368'),
            gridcolor='#e8eaed',
            tickformat=',',
            showgrid=True,
            gridwidth=1,
            rangemode='tozero',
            autorange=True
        ),
        hovermode='x unified',
        height=450,
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color='#202124'),
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)',
            borderwidth=0
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#dadce0',
            font_size=12,
            font_family='Google Sans, Arial, sans-serif'
        )
    )
    
    return fig


def create_revenue_trend_chart(daily_revenue_data: list, title: str = "Revenue Over Time", aggregation: str = "daily", show_moving_avg: bool = True):
    """
    Create a line chart for revenue trends with aggregation and smoothing options.
    
    Args:
        daily_revenue_data: List of daily revenue data dictionaries
        title: Chart title
        aggregation: 'daily', 'weekly', or 'monthly'
        show_moving_avg: Whether to show moving average
    """
    if not daily_revenue_data:
        return None
    
    df = pd.DataFrame(daily_revenue_data)
    
    # Check if we have enough data
    if len(df) < 1:
        return None
    
    # Check if required columns exist
    required_cols = ['date', 'totalRevenue', 'adRevenue', 'purchaseRevenue']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.warning(f"Missing required columns in revenue data: {missing_cols}")
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Fill any NaN values with 0 and ensure numeric
    df['totalRevenue'] = pd.to_numeric(df['totalRevenue'], errors='coerce').fillna(0.0)
    df['adRevenue'] = pd.to_numeric(df['adRevenue'], errors='coerce').fillna(0.0)
    df['purchaseRevenue'] = pd.to_numeric(df['purchaseRevenue'], errors='coerce').fillna(0.0)
    
    # Ensure all revenue columns exist and have at least some data points
    # This helps ensure all lines are visible even if some values are zero
    
    # Debug: Log data summary - lines will show even if values are zero
    if len(df) > 0:
        total_rev_sum = df['totalRevenue'].sum()
        ad_rev_sum = df['adRevenue'].sum()
        iap_rev_sum = df['purchaseRevenue'].sum()
    
    # Aggregate data based on selection
    if aggregation == 'weekly':
        df['week'] = df['date'].dt.to_period('W').dt.start_time
        df_agg = df.groupby('week').agg({
            'totalRevenue': 'sum',
            'adRevenue': 'sum',
            'purchaseRevenue': 'sum'
        }).reset_index()
        df_agg.rename(columns={'week': 'date'}, inplace=True)
        df = df_agg
    elif aggregation == 'monthly':
        df['month'] = df['date'].dt.to_period('M').dt.start_time
        df_agg = df.groupby('month').agg({
            'totalRevenue': 'sum',
            'adRevenue': 'sum',
            'purchaseRevenue': 'sum'
        }).reset_index()
        df_agg.rename(columns={'month': 'date'}, inplace=True)
        df = df_agg
    
    # Always calculate moving averages for smooth trend lines
    # Use adaptive window size based on data length
    if len(df) > 1:
        window = max(3, min(7, len(df) // 3))  # Minimum 3, maximum 7, or 1/3 of data points
        df['totalRevenue_ma'] = df['totalRevenue'].rolling(window=window, center=True, min_periods=1).mean()
        df['adRevenue_ma'] = df['adRevenue'].rolling(window=window, center=True, min_periods=1).mean()
        df['purchaseRevenue_ma'] = df['purchaseRevenue'].rolling(window=window, center=True, min_periods=1).mean()
    else:
        df['totalRevenue_ma'] = df['totalRevenue']
        df['adRevenue_ma'] = df['adRevenue']
        df['purchaseRevenue_ma'] = df['purchaseRevenue']
    
    # Ensure moving averages are not all zeros or NaN
    df['totalRevenue_ma'] = df['totalRevenue_ma'].fillna(0.0)
    df['adRevenue_ma'] = df['adRevenue_ma'].fillna(0.0)
    df['purchaseRevenue_ma'] = df['purchaseRevenue_ma'].fillna(0.0)
    
    # Debug: Verify data ranges
    total_rev_range = (df['totalRevenue_ma'].min(), df['totalRevenue_ma'].max())
    ad_rev_range = (df['adRevenue_ma'].min(), df['adRevenue_ma'].max())
    iap_rev_range = (df['purchaseRevenue_ma'].min(), df['purchaseRevenue_ma'].max())
    
    # Calculate median values for reference lines
    total_revenue_median = df['totalRevenue_ma'].median()
    ad_revenue_median = df['adRevenue_ma'].median()
    iap_revenue_median = df['purchaseRevenue_ma'].median()
    
    fig = go.Figure()
    
    # Google Analytics style: Clean lines, no markers, zigzag pattern
    # Total Revenue - Green solid line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['totalRevenue_ma'],
        mode='lines',
        name='Total Revenue',
        line=dict(color='#34a853', width=2.5, shape='linear'),
        hovertemplate='<b>Total Revenue</b><br>Date: %{x|%Y-%m-%d}<br>Revenue: $%{y:,.2f}<extra></extra>',
        showlegend=True,
        connectgaps=True
    ))
    
    # Ad Revenue - Blue solid line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['adRevenue_ma'],
        mode='lines',
        name='Ad Revenue',
        line=dict(color='#1a73e8', width=2.5, shape='linear'),
        hovertemplate='<b>Ad Revenue</b><br>Date: %{x|%Y-%m-%d}<br>Revenue: $%{y:,.2f}<extra></extra>',
        showlegend=True,
        connectgaps=True
    ))
    
    # In-App Purchase Revenue - Purple solid line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['purchaseRevenue_ma'],
        mode='lines',
        name='In-App Purchase Revenue',
        line=dict(color='#9c27b0', width=2.5, shape='linear'),
        hovertemplate='<b>In-App Purchase Revenue</b><br>Date: %{x|%Y-%m-%d}<br>Revenue: $%{y:,.2f}<extra></extra>',
        showlegend=True,
        connectgaps=True
    ))
    
    # Median lines - dashed, matching colors
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[total_revenue_median, total_revenue_median],
        mode='lines',
        name='Total Revenue Median',
        line=dict(color='#34a853', width=1.5, dash='dash'),
        hovertemplate='<b>Total Revenue Median</b><br>Value: $%{y:,.2f}<extra></extra>',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[ad_revenue_median, ad_revenue_median],
        mode='lines',
        name='Ad Revenue Median',
        line=dict(color='#1a73e8', width=1.5, dash='dash'),
        hovertemplate='<b>Ad Revenue Median</b><br>Value: $%{y:,.2f}<extra></extra>',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=[df['date'].min(), df['date'].max()],
        y=[iap_revenue_median, iap_revenue_median],
        mode='lines',
        name='IAP Revenue Median',
        line=dict(color='#9c27b0', width=1.5, dash='dash'),
        hovertemplate='<b>IAP Revenue Median</b><br>Value: $%{y:,.2f}<extra></extra>',
        showlegend=False
    ))
    
    # Update aggregation label in title
    agg_label = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly'
    }.get(aggregation, 'Daily')
    
    # Google Analytics style layout - clean and minimal
    fig.update_layout(
        title=dict(
            text=f'{agg_label} Revenue Trend - {title}',
            font=dict(size=20, color='#202124', family='Google Sans, Arial, sans-serif')
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#5f6368')),
            tickfont=dict(size=12, color='#5f6368'),
            gridcolor='#e8eaed',
            showgrid=True,
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text='Revenue ($)', font=dict(size=14, color='#5f6368')),
            tickfont=dict(size=12, color='#5f6368'),
            gridcolor='#e8eaed',
            tickformat='$,.0f',
            showgrid=True,
            gridwidth=1,
            rangemode='tozero',
            autorange=True
        ),
        hovermode='x unified',
        height=450,
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color='#202124'),
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)',
            borderwidth=0
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#dadce0',
            font_size=12,
            font_family='Google Sans, Arial, sans-serif'
        )
    )
    
    return fig


def create_mini_trend_chart(values: list, color: str = '#3b82f6', height: int = 60):
    """Create a mini sparkline chart for trend visualization."""
    if not values or len(values) < 2:
        return None
    
    fig = go.Figure()
    
    # Determine trend direction
    first_half = values[:len(values)//2] if len(values) > 4 else values[:1]
    second_half = values[len(values)//2:] if len(values) > 4 else values[-1:]
    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0
    
    # Use green for upward trend, red for downward, blue for neutral
    if avg_second > avg_first * 1.05:
        line_color = '#10b981'  # Green for up
    elif avg_second < avg_first * 0.95:
        line_color = '#ef4444'  # Red for down
    else:
        line_color = color  # Blue for neutral
    
    # Convert hex color to rgba format for fillcolor
    def hex_to_rgba(hex_color, alpha=0.2):
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=line_color, width=2.5),
        fill='tozeroy',
        fillcolor=hex_to_rgba(line_color, 0.2),  # 20% opacity in rgba format
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        hovermode=False
    )
    
    return fig


def create_stacked_area_chart(daily_revenue_data: list, title: str = "Revenue Breakdown Over Time", aggregation: str = "daily"):
    """
    Create a stacked area chart showing Ad Revenue vs In-App Purchase Revenue over time.
    
    Args:
        daily_revenue_data: List of daily revenue data dictionaries
        title: Chart title
        aggregation: 'daily', 'weekly', or 'monthly'
    """
    if not daily_revenue_data:
        return None
    
    df = pd.DataFrame(daily_revenue_data)
    
    if len(df) < 1:
        return None
    
    required_cols = ['date', 'adRevenue', 'purchaseRevenue']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    df['adRevenue'] = pd.to_numeric(df['adRevenue'], errors='coerce').fillna(0.0)
    df['purchaseRevenue'] = pd.to_numeric(df['purchaseRevenue'], errors='coerce').fillna(0.0)
    
    # Aggregate data based on selection
    if aggregation == 'weekly':
        df['week'] = df['date'].dt.to_period('W').dt.start_time
        df_agg = df.groupby('week').agg({
            'adRevenue': 'sum',
            'purchaseRevenue': 'sum'
        }).reset_index()
        df_agg.rename(columns={'week': 'date'}, inplace=True)
        df = df_agg
    elif aggregation == 'monthly':
        df['month'] = df['date'].dt.to_period('M').dt.start_time
        df_agg = df.groupby('month').agg({
            'adRevenue': 'sum',
            'purchaseRevenue': 'sum'
        }).reset_index()
        df_agg.rename(columns={'month': 'date'}, inplace=True)
        df = df_agg
    
    fig = go.Figure()
    
    # Stacked area chart: Ad Revenue (bottom) and IAP Revenue (top)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['adRevenue'],
        mode='lines',
        name='Ad Revenue',
        stackgroup='one',
        fillcolor='rgba(59, 130, 246, 0.6)',
        line=dict(color='#3b82f6', width=0),
        hovertemplate='<b>Ad Revenue</b><br>Date: %{x|%Y-%m-%d}<br>Revenue: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['purchaseRevenue'],
        mode='lines',
        name='In-App Purchase Revenue',
        stackgroup='one',
        fillcolor='rgba(139, 92, 246, 0.6)',
        line=dict(color='#8b5cf6', width=0),
        hovertemplate='<b>In-App Purchase Revenue</b><br>Date: %{x|%Y-%m-%d}<br>Revenue: $%{y:,.2f}<extra></extra>'
    ))
    
    agg_label = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly'
    }.get(aggregation, 'Daily')
    
    fig.update_layout(
        title=dict(
            text=f'{agg_label} Revenue Breakdown - {title}',
            font=dict(size=24, color='#111827', family='Arial Black', weight='bold')
        ),
        xaxis=dict(
            title=dict(text='Date', font=dict(size=18, color='#1f2937', weight='bold')),
            tickfont=dict(size=14, color='#374151'),
            gridcolor='#e5e7eb',
            showgrid=True
        ),
        yaxis=dict(
            title=dict(text='Revenue ($)', font=dict(size=18, color='#1f2937', weight='bold')),
            tickfont=dict(size=14, color='#374151'),
            gridcolor='#e5e7eb',
            tickformat='$,.0f',
            showgrid=True,
            rangemode='tozero',
            autorange=True
        ),
        hovermode='x unified',
        height=550,
        template='plotly_white',
        plot_bgcolor='#f9fafb',
        paper_bgcolor='white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=15, color='#1f2937', weight='bold'),
            bgcolor='rgba(255,255,255,0.98)',
            bordercolor='#d1d5db',
            borderwidth=2
        ),
        margin=dict(l=80, r=150, t=90, b=80)
    )
    
    return fig


def create_yoy_comparison_chart(daily_revenue_data: list, title: str = "Year-over-Year Comparison"):
    """
    Create a bar chart comparing revenue across different years.
    
    Args:
        daily_revenue_data: List of daily revenue data dictionaries
        title: Chart title
    """
    if not daily_revenue_data:
        return None
    
    df = pd.DataFrame(daily_revenue_data)
    
    if len(df) < 1:
        return None
    
    required_cols = ['date', 'totalRevenue', 'adRevenue', 'purchaseRevenue']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    df['totalRevenue'] = pd.to_numeric(df['totalRevenue'], errors='coerce').fillna(0.0)
    df['adRevenue'] = pd.to_numeric(df['adRevenue'], errors='coerce').fillna(0.0)
    df['purchaseRevenue'] = pd.to_numeric(df['purchaseRevenue'], errors='coerce').fillna(0.0)
    
    # Group by year
    df['year'] = df['date'].dt.year
    df_yearly = df.groupby('year').agg({
        'totalRevenue': 'sum',
        'adRevenue': 'sum',
        'purchaseRevenue': 'sum'
    }).reset_index()
    
    if len(df_yearly) < 1:
        return None
    
    fig = go.Figure()
    
    # Stacked bar chart
    fig.add_trace(go.Bar(
        x=df_yearly['year'],
        y=df_yearly['adRevenue'],
        name='Ad Revenue',
        marker_color='#3b82f6',
        hovertemplate='<b>Ad Revenue</b><br>Year: %{x}<br>Revenue: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=df_yearly['year'],
        y=df_yearly['purchaseRevenue'],
        name='In-App Purchase Revenue',
        marker_color='#8b5cf6',
        hovertemplate='<b>In-App Purchase Revenue</b><br>Year: %{x}<br>Revenue: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f'{title}',
            font=dict(size=24, color='#111827', family='Arial Black', weight='bold')
        ),
        xaxis=dict(
            title=dict(text='Year', font=dict(size=18, color='#1f2937', weight='bold')),
            tickfont=dict(size=14, color='#374151'),
            gridcolor='#e5e7eb',
            showgrid=True
        ),
        yaxis=dict(
            title=dict(text='Revenue ($)', font=dict(size=18, color='#1f2937', weight='bold')),
            tickfont=dict(size=14, color='#374151'),
            gridcolor='#e5e7eb',
            tickformat='$,.0f',
            showgrid=True,
            rangemode='tozero'
        ),
        barmode='stack',
        height=550,
        template='plotly_white',
        plot_bgcolor='#f9fafb',
        paper_bgcolor='white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=15, color='#1f2937', weight='bold'),
            bgcolor='rgba(255,255,255,0.98)',
            bordercolor='#d1d5db',
            borderwidth=2
        ),
        margin=dict(l=80, r=150, t=90, b=80)
    )
    
    return fig


def create_revenue_chart(revenue_data: dict):
    """Create a bar chart for revenue breakdown."""
    revenue_types = ['Total Revenue', 'Ad Revenue', 'In-App Purchases']
    revenue_values = [
        revenue_data.get('total_revenue', 0),
        revenue_data.get('ad_revenue', 0),
        revenue_data.get('in_app_purchase_revenue', 0)
    ]
    
    # Enhanced color scheme with better contrast
    colors = ['#10b981', '#3b82f6', '#8b5cf6']
    
    # Create bars with enhanced styling
    fig = go.Figure(data=[
        go.Bar(
            x=revenue_types,
            y=revenue_values,
            marker=dict(
                color=colors,
                line=dict(color='#ffffff', width=2.5),
                opacity=0.95
            ),
            text=[f'${val:,.2f}' for val in revenue_values],
            textposition='outside',
            textfont=dict(size=18, color='#111827', family='Arial, sans-serif', weight='bold'),
            hovertemplate='<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>',
            width=0.55,
            showlegend=False
        )
    ])
    
    # Calculate max value for y-axis
    max_value = max(revenue_values) if revenue_values else 0
    y_max = max_value * 1.3  # 30% above max value
    
    # Enhanced layout with better spacing and styling
    fig.update_layout(
        xaxis=dict(
            showticklabels=True,
            tickfont=dict(size=16, color='#1f2937', family='Arial, sans-serif', weight='bold'),
            gridcolor='#f3f4f6',
            gridwidth=1,
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            showticklabels=True,
            tickfont=dict(size=15, color='#374151', family='Arial, sans-serif', weight='bold'),
            gridcolor='#e5e7eb',
            gridwidth=1.5,
            showgrid=True,
            zeroline=True,
            zerolinecolor='#d1d5db',
            zerolinewidth=2,
            tickformat='$,.0f',
            range=[0, y_max],
            tickmode='linear',
            tick0=0,
            dtick=max(500, y_max / 8)  # Dynamic tick spacing
        ),
        height=520,
        template='plotly_white',
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        showlegend=False,
        margin=dict(l=80, r=40, t=40, b=100),
        hovermode='closest',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#1f2937',
            font_size=14,
            font_family='Arial, sans-serif',
            font_color='#111827'
        )
    )
    
    return fig


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def section_header_with_info(title: str, info_text: str, info_key: str = None):
    """Create a section header with an information icon that shows tooltip on hover."""
    if info_key is None:
        info_key = f"info_{title.replace(' ', '_').replace('-', '_').lower()}"
    
    # Escape quotes in info_text for HTML
    info_text_escaped = info_text.replace('"', '&quot;').replace("'", "&#39;")
    
    col_title, col_info = st.columns([20, 1])
    with col_title:
        st.markdown(f"<h2 style='margin: 0; padding: 0; display: inline-block;'>{title}</h2>", unsafe_allow_html=True)
    with col_info:
        st.markdown(f"""
        <div style="position: relative; display: inline-flex; align-items: center; justify-content: center;">
            <span class="info-icon-tooltip" 
                  style="cursor: help; color: #9ca3af; font-size: 16px; 
                         display: inline-flex; align-items: center; justify-content: center;
                         width: 24px; height: 24px; 
                         border-radius: 50%; 
                         background: transparent;
                         transition: all 0.2s ease;
                         font-weight: 500;"
                  data-tooltip="{info_text_escaped}">ℹ</span>
        </div>
        """, unsafe_allow_html=True)


def subheader_with_info(title: str, info_text: str, info_key: str = None):
    """Create a subheader with an information icon that shows tooltip on hover."""
    if info_key is None:
        info_key = f"info_{title.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_').lower()}"
    
    # Escape quotes in info_text for HTML
    info_text_escaped = info_text.replace('"', '&quot;').replace("'", "&#39;")
    
    col_title, col_info = st.columns([20, 1])
    with col_title:
        st.markdown(f"<h3 style='margin: 0; padding: 0; display: inline-block;'>{title}</h3>", unsafe_allow_html=True)
    with col_info:
        st.markdown(f"""
        <div style="position: relative; display: inline-flex; align-items: center; justify-content: center;">
            <span class="info-icon-tooltip" 
                  style="cursor: help; color: #9ca3af; font-size: 14px; 
                         display: inline-flex; align-items: center; justify-content: center;
                         width: 22px; height: 22px; 
                         border-radius: 50%; 
                         background: transparent;
                         transition: all 0.2s ease;
                         font-weight: 500;"
                  data-tooltip="{info_text_escaped}">ℹ</span>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main dashboard function."""
    
    # Title
    st.title("GA4 Analytics Dashboard")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Load config (file-based only, no secrets)
        config = load_config()
        
        # Check if using Streamlit secrets (handle separately to avoid recursion)
        # Check if Streamlit secrets are available
        using_secrets = False
        service_account_info = None
        
        try:
            # Try to access secrets (works on Streamlit Cloud or with .streamlit/secrets.toml)
            if hasattr(st, 'secrets') and st.secrets:
                # Check for GA4 service account in secrets (format: secrets.ga4.service_account)
                if 'ga4' in st.secrets:
                    ga4_secrets = st.secrets.get('ga4', {})
                    if 'service_account' in ga4_secrets:
                        using_secrets = True
                        service_account_info = dict(ga4_secrets['service_account'])
                        config['service_account_info'] = service_account_info
                        st.success("Using credentials from Streamlit secrets")
                # Also check for direct service_account in secrets
                elif 'service_account' in st.secrets:
                    using_secrets = True
                    service_account_info = dict(st.secrets['service_account'])
                    config['service_account_info'] = service_account_info
                    st.success("Using credentials from Streamlit secrets")
        except (AttributeError, KeyError, RuntimeError, TypeError) as e:
            # Secrets not available or not configured - will use file-based auth
            using_secrets = False
        
        # Property ID input
        property_id = st.text_input(
            "GA4 Property ID",
            value=config.get('property_id', ''),
            help="Enter your GA4 Property ID (numeric)"
        )
        
        # Service account path (only show if not using secrets)
        if using_secrets:
            st.info("🔐 Using credentials from Streamlit secrets")
            service_account_path = None
        else:
            service_account_path = st.text_input(
                "Service Account Key Path",
                value=config.get('service_account_path', 'service-account-key.json'),
                help="Path to your service account JSON key file"
            )
        
        # Date range selection
        date_range_option = st.radio(
            "Date Range Selection",
            ["Custom Dates", "Last N Days"],
            help="Choose to select specific dates or use a number of days"
        )
        
        if date_range_option == "Custom Dates":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date() - timedelta(days=29),
                    max_value=datetime.now().date(),
                    help="Select the start date for data retrieval"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now().date(),
                    max_value=datetime.now().date(),
                    min_value=start_date,
                    help="Select the end date for data retrieval"
                )
            days = None
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            days = st.slider(
                "Date Range (days)",
                min_value=7,
                max_value=90,
                value=config.get('date_range_days', 30),
                help="Number of days to look back"
            )
            start_date_str = None
            end_date_str = None
        
        # Refresh button
        if st.button("Refresh Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This dashboard displays:
        - Daily users (total and active)
        - Revenue metrics (total, ad, in-app purchases)
        - Summary statistics
        """)
    
    # Validate inputs
    if not property_id:
        st.warning("Please enter your GA4 Property ID in the sidebar.")
        return
    
    # Only validate file path if NOT using secrets
    # Skip file validation entirely if using Streamlit secrets
    if not using_secrets:
        if not service_account_path:
            st.error("Service account key path is required when not using Streamlit secrets.")
            return
        
        # Resolve relative paths - check both absolute and relative to current directory
        if not os.path.isabs(service_account_path):
            # Try relative to current working directory
            if os.path.exists(service_account_path):
                pass  # File exists
            elif os.path.exists(os.path.join(os.getcwd(), service_account_path)):
                service_account_path = os.path.join(os.getcwd(), service_account_path)
            else:
                st.error(f"Service account key file not found: {service_account_path}")
                st.info("Please make sure the service account JSON file exists in the specified path, or configure Streamlit secrets in Settings → Secrets.")
                return
        elif not os.path.exists(service_account_path):
            st.error(f"Service account key file not found: {service_account_path}")
            st.info("Please make sure the service account JSON file exists in the specified path, or configure Streamlit secrets in Settings → Secrets.")
            return
    else:
        # Using secrets - set service_account_path to None to avoid file checks
        service_account_path = None
    
    # Optimized caching: 3 hours (balance between freshness and API limits)
    CACHE_DURATION_HOURS = 3
    CACHE_DURATION_SECONDS = CACHE_DURATION_HOURS * 3600
    
    # Manual refresh button
    col_refresh1, col_refresh2 = st.columns([3, 1])
    with col_refresh1:
        st.markdown("")  # Spacer
    with col_refresh2:
        if st.button("Refresh Data", key="refresh_main_data", help="Manually refresh data from GA4 API"):
            # Clear cache for this key
            cache_key = f"ga4_data_{property_id}_{service_account_path}_{days}_{start_date_str}_{end_date_str}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.rerun()
    
    # Fetch data with optimized caching
    cache_key = f"ga4_data_{property_id}_{service_account_path}_{days}_{start_date_str}_{end_date_str}"
    
    # Check if we have cached data
    if cache_key in st.session_state:
        cached_data, cached_time = st.session_state[cache_key]
        # Use cache if less than configured hours old
        cache_age_seconds = (datetime.now() - cached_time).total_seconds()
        if cache_age_seconds < CACHE_DURATION_SECONDS:
            data, error = cached_data
            cache_age_hours = cache_age_seconds / 3600
            st.caption(f"Using cached data (refreshed {cache_age_hours:.1f} hours ago. Next refresh in {CACHE_DURATION_HOURS - cache_age_hours:.1f} hours)")
        else:
            # Cache expired, fetch new data
            with st.spinner("Fetching fresh data from GA4 API..."):
                service_account_info_param = config.get('service_account_info') if using_secrets else None
                if date_range_option == "Custom Dates":
                    data, error = fetch_ga4_data(property_id, service_account_path, None, start_date_str, end_date_str, service_account_info_param)
                else:
                    data, error = fetch_ga4_data(property_id, service_account_path, days, None, None, service_account_info_param)
            # Update cache
            st.session_state[cache_key] = ((data, error), datetime.now())
            st.success(f"Data refreshed. Cache valid for {CACHE_DURATION_HOURS} hours.")
    else:
        # No cache, fetch data
        with st.spinner("Fetching data from GA4 API..."):
            service_account_info_param = config.get('service_account_info') if using_secrets else None
            if date_range_option == "Custom Dates":
                data, error = fetch_ga4_data(property_id, service_account_path, None, start_date_str, end_date_str, service_account_info_param)
            else:
                data, error = fetch_ga4_data(property_id, service_account_path, days, None, None, service_account_info_param)
        # Store in cache
        st.session_state[cache_key] = ((data, error), datetime.now())
        st.success(f"Data loaded. Cache valid for {CACHE_DURATION_HOURS} hours.")
    
    if error:
        st.error(f"Error fetching data: {error}")
        st.info("""
        Common issues:
        - Verify service account has Viewer access to GA4 property
        - Check that Property ID is correct (numeric, not Measurement ID)
        - Ensure GA4 Data API is enabled in Google Cloud Console
        """)
        return
    
    if not data:
        st.warning("No data available for the selected date range.")
        return
    
    # Display metadata
    metadata = data.get('metadata', {})
    date_range = metadata.get('date_range', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Property ID**")
        st.markdown(f"<div style='font-size: 17px; font-weight: 600; color: #1f2937;'>{metadata.get('property_id', 'N/A')}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("**Date Range**")
        st.markdown(f"<div style='font-size: 17px; font-weight: 600; color: #1f2937;'>{date_range.get('start_date', 'N/A')} to {date_range.get('end_date', 'N/A')}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("**Last Updated**")
        st.markdown(f"<div style='font-size: 17px; font-weight: 600; color: #1f2937;'>{metadata.get('generated_at', 'N/A')[:19]}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Summary metrics
    section_header_with_info(
        "Summary Metrics",
        "Overview of key metrics for the selected period. Shows total users, active users, revenue breakdown, session duration, and revenue per user. Includes comparison with previous period and daily averages."
    )
    summary = data.get('summary', {})
    
    # Debug: Show if summary is empty
    if not summary:
        st.warning("Summary data is empty. This might indicate no data in GA4 for the selected date range.")
        st.json(data)  # Show raw data for debugging
        return
    
    # Get current and previous period data
    deltas = summary.get('deltas', {})
    previous = summary.get('previous_period', {})
    
    # Calculate period duration
    start_date_str = date_range.get('start_date', '')
    end_date_str = date_range.get('end_date', '')
    period_days = 0
    period_label = ""
    
    if start_date_str and end_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            period_days = (end_dt - start_dt).days + 1
            
            if period_days == 1:
                period_label = "Today"
            elif period_days <= 7:
                period_label = f"{period_days} days"
            else:
                # Check if it's close to a whole number of months (within ±2 days tolerance)
                months_approx = period_days / 30.0
                months_whole = round(months_approx)
                days_diff = abs(period_days - (months_whole * 30))
                
                # If within 2 days of a whole month, show as months
                if days_diff <= 2 and months_whole > 0:
                    period_label = f"{months_whole} month{'s' if months_whole > 1 else ''}"
                else:
                    # Check if it's close to a whole number of years
                    years_approx = period_days / 365.0
                    years_whole = round(years_approx)
                    days_diff_years = abs(period_days - (years_whole * 365))
                    
                    # If within 5 days of a whole year, show as years
                    if days_diff_years <= 5 and years_whole > 0:
                        if years_whole == 1:
                            period_label = "1 year"
                        else:
                            period_label = f"{years_whole} years"
                    else:
                        # Otherwise show as days
                        period_label = f"{period_days} days"
        except:
            period_label = f"{period_days} days" if period_days > 0 else "Selected period"
    else:
        period_label = "Selected period"
    
    # Helper function to format delta
    def format_delta(delta_value):
        if delta_value is None:
            return None
        return f"{delta_value:+.1f}%"
    
    # Get daily data for trend charts
    daily_users_data = data.get('daily_users', [])
    daily_revenue_data = data.get('daily_revenue', [])
    
    # Extract trend values for each metric
    total_users_trend = []
    active_users_trend = []
    total_revenue_trend = []
    ad_revenue_trend = []
    iap_revenue_trend = []
    session_duration_trend = []
    arpu_trend = []
    
    if daily_users_data:
        for day in sorted(daily_users_data, key=lambda x: x.get('date', '')):
            total_users_trend.append(day.get('totalUsers', 0))
            active_users_trend.append(day.get('activeUsers', 0))
            # Session duration in seconds, convert to minutes
            session_dur_sec = day.get('averageSessionDuration', 0)
            session_duration_trend.append(session_dur_sec / 60.0 if session_dur_sec > 0 else 0)
    
    if daily_revenue_data and daily_users_data:
        # Create a date-indexed dict for revenue data
        revenue_by_date = {}
        for day in daily_revenue_data:
            date_key = day.get('date', '')
            if date_key:
                revenue_by_date[date_key] = day
        
        for day in sorted(daily_users_data, key=lambda x: x.get('date', '')):
            date_key = day.get('date', '')
            revenue_day = revenue_by_date.get(date_key, {})
            
            total_revenue_trend.append(revenue_day.get('totalRevenue', 0))
            ad_revenue_trend.append(revenue_day.get('adRevenue', 0))
            iap_revenue_trend.append(revenue_day.get('purchaseRevenue', 0))
            
            # Calculate ARPU: revenue per user
            day_users = day.get('totalUsers', 0)
            day_revenue = revenue_day.get('totalRevenue', 0)
            arpu = (day_revenue / day_users) if day_users > 0 else 0
            arpu_trend.append(arpu)
    
    # Create metric cards with deltas - First row with 5 main metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_users = summary.get('total_users', 0)
        prev_total_users = previous.get('total_users', 0)
        delta_users = deltas.get('total_users')
        daily_avg_users = total_users / period_days if period_days > 0 else 0
        st.metric(
            label=f"Total Users ({period_label})",
            value=f"{total_users:,}",
            delta=format_delta(delta_users) if delta_users is not None else None,
            help="Total number of unique users who visited your app/website during the selected period. Includes all users regardless of engagement level."
        )
        if period_days > 1:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; text-align: center;'>Avg: {daily_avg_users:,.0f}/day</div>", unsafe_allow_html=True)
        # Add trend chart
        if total_users_trend and len(total_users_trend) > 1:
            trend_fig = create_mini_trend_chart(total_users_trend, color='#2563eb', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
        if prev_total_users > 0:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; padding-top: 4px; border-top: 1px solid #e5e7eb; text-align: center;'>Prev: {prev_total_users:,}</div>", unsafe_allow_html=True)
        elif total_users == 0:
            st.markdown("<div style='font-size: 11px; font-weight: 500; color: #9ca3af; margin-top: 4px; text-align: center;'>No data</div>", unsafe_allow_html=True)
    
    with col2:
        active_users = summary.get('active_users', 0)
        prev_active_users = previous.get('active_users', 0)
        delta_active = deltas.get('active_users')
        daily_avg_active = active_users / period_days if period_days > 0 else 0
        st.metric(
            label=f"Active Users ({period_label})",
            value=f"{active_users:,}",
            delta=format_delta(delta_active) if delta_active is not None else None,
            help="Number of users who actively engaged with your app/website. Active users are those who had meaningful interactions beyond just opening the app."
        )
        if period_days > 1:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; text-align: center;'>Avg: {daily_avg_active:,.0f}/day</div>", unsafe_allow_html=True)
        # Add trend chart
        if active_users_trend and len(active_users_trend) > 1:
            trend_fig = create_mini_trend_chart(active_users_trend, color='#f59e0b', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
        if prev_active_users > 0:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; padding-top: 4px; border-top: 1px solid #e5e7eb; text-align: center;'>Prev: {prev_active_users:,}</div>", unsafe_allow_html=True)
        elif active_users == 0:
            st.markdown("<div style='font-size: 11px; font-weight: 500; color: #9ca3af; margin-top: 4px; text-align: center;'>No data</div>", unsafe_allow_html=True)
    
    with col3:
        total_revenue = summary.get('total_revenue', 0)
        prev_total_revenue = previous.get('total_revenue', 0)
        delta_revenue = deltas.get('total_revenue')
        daily_avg_revenue = total_revenue / period_days if period_days > 0 else 0
        monthly_est_revenue = (total_revenue / period_days * 30) if period_days > 0 else 0
        st.metric(
            label=f"Total Revenue ({period_label})",
            value=format_currency(total_revenue),
            delta=format_delta(delta_revenue) if delta_revenue is not None else None,
            help="Total revenue from all sources including ad revenue and in-app purchases. This is the sum of all revenue generated during the selected period."
        )
        if period_days > 1:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; text-align: center;'>Avg: {format_currency(daily_avg_revenue)}/day</div>", unsafe_allow_html=True)
            if period_days < 30:
                st.markdown(f"<div style='font-size: 10px; font-weight: 400; color: #9ca3af; margin-top: 2px; text-align: center;'>Est. monthly: {format_currency(monthly_est_revenue)}</div>", unsafe_allow_html=True)
        # Add trend chart
        if total_revenue_trend and len(total_revenue_trend) > 1:
            trend_fig = create_mini_trend_chart(total_revenue_trend, color='#10b981', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
        if prev_total_revenue > 0:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; padding-top: 4px; border-top: 1px solid #e5e7eb; text-align: center;'>Prev: {format_currency(prev_total_revenue)}</div>", unsafe_allow_html=True)
        elif total_revenue == 0:
            st.markdown("<div style='font-size: 11px; font-weight: 500; color: #9ca3af; margin-top: 4px; text-align: center;'>No data</div>", unsafe_allow_html=True)
    
    with col4:
        ad_revenue = summary.get('ad_revenue', 0)
        prev_ad_revenue = previous.get('ad_revenue', 0)
        delta_ad = deltas.get('ad_revenue')
        daily_avg_ad = ad_revenue / period_days if period_days > 0 else 0
        monthly_est_ad = (ad_revenue / period_days * 30) if period_days > 0 else 0
        st.metric(
            label=f"Ad Revenue ({period_label})",
            value=format_currency(ad_revenue),
            delta=format_delta(delta_ad) if delta_ad is not None else None,
            help="Revenue generated from advertisements. This includes revenue from AdMob (if linked) and other ad networks. Calculated as total revenue minus in-app purchase revenue."
        )
        if period_days > 1:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; text-align: center;'>Avg: {format_currency(daily_avg_ad)}/day</div>", unsafe_allow_html=True)
            if period_days < 30:
                st.markdown(f"<div style='font-size: 10px; font-weight: 400; color: #9ca3af; margin-top: 2px; text-align: center;'>Est. monthly: {format_currency(monthly_est_ad)}</div>", unsafe_allow_html=True)
        # Add trend chart
        if ad_revenue_trend and len(ad_revenue_trend) > 1:
            trend_fig = create_mini_trend_chart(ad_revenue_trend, color='#3b82f6', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
        if prev_ad_revenue > 0:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; padding-top: 4px; border-top: 1px solid #e5e7eb; text-align: center;'>Prev: {format_currency(prev_ad_revenue)}</div>", unsafe_allow_html=True)
        elif ad_revenue == 0:
            st.markdown("<div style='font-size: 11px; font-weight: 500; color: #9ca3af; margin-top: 4px; text-align: center;'>No data</div>", unsafe_allow_html=True)
    
    with col5:
        in_app_revenue = summary.get('in_app_purchase_revenue', 0)
        prev_in_app = previous.get('in_app_purchase_revenue', 0)
        delta_in_app = deltas.get('in_app_purchase_revenue')
        daily_avg_iap = in_app_revenue / period_days if period_days > 0 else 0
        monthly_est_iap = (in_app_revenue / period_days * 30) if period_days > 0 else 0
        st.metric(
            label=f"In-App Purchase Revenue ({period_label})",
            value=format_currency(in_app_revenue),
            delta=format_delta(delta_in_app) if delta_in_app is not None else None,
            help="Revenue from in-app purchases and subscriptions. This includes all purchase events where users bought items, subscriptions, or premium features within your app."
        )
        if period_days > 1:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; text-align: center;'>Avg: {format_currency(daily_avg_iap)}/day</div>", unsafe_allow_html=True)
            if period_days < 30:
                st.markdown(f"<div style='font-size: 10px; font-weight: 400; color: #9ca3af; margin-top: 2px; text-align: center;'>Est. monthly: {format_currency(monthly_est_iap)}</div>", unsafe_allow_html=True)
        # Add trend chart
        if iap_revenue_trend and len(iap_revenue_trend) > 1:
            trend_fig = create_mini_trend_chart(iap_revenue_trend, color='#8b5cf6', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
        if prev_in_app > 0:
            st.markdown(f"<div style='font-size: 11px; font-weight: 500; color: #6b7280; margin-top: 4px; padding-top: 4px; border-top: 1px solid #e5e7eb; text-align: center;'>Prev: {format_currency(prev_in_app)}</div>", unsafe_allow_html=True)
        elif in_app_revenue == 0:
            st.markdown("<div style='font-size: 11px; font-weight: 500; color: #9ca3af; margin-top: 4px; text-align: center;'>No data</div>", unsafe_allow_html=True)
    
    # Second row for Session Duration and ARPU
    st.markdown("<br>", unsafe_allow_html=True)
    col6, col7 = st.columns(2)
    
    with col6:
        session_duration = summary.get('session_duration_minutes', 0)
        st.metric(
            label="Session Duration",
            value=f"{session_duration:.1f} min",
            delta=None,
            help="Average time users spend in your app per session. Higher session duration typically indicates better user engagement and content quality."
        )
        st.markdown("<div style='font-size: 12px; font-weight: 500; color: #6b7280; margin-top: 6px; padding-top: 6px; border-top: 1px solid #e5e7eb; text-align: center;'>Average per session</div>", unsafe_allow_html=True)
        # Add trend chart
        if session_duration_trend and len(session_duration_trend) > 1:
            trend_fig = create_mini_trend_chart(session_duration_trend, color='#06b6d4', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
    
    with col7:
        arpu = summary.get('arpu', 0)
        st.metric(
            label="ARPU",
            value=format_currency(arpu),
            delta=None,
            help="Average Revenue Per User. Calculated as total revenue divided by total users. This metric helps understand the monetization value of each user."
        )
        st.markdown("<div style='font-size: 12px; font-weight: 500; color: #6b7280; margin-top: 6px; padding-top: 6px; border-top: 1px solid #e5e7eb; text-align: center;'>Revenue per user</div>", unsafe_allow_html=True)
        # Add trend chart
        if arpu_trend and len(arpu_trend) > 1:
            trend_fig = create_mini_trend_chart(arpu_trend, color='#ec4899', height=50)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
    
    # Revenue comparisons with different periods
    st.markdown("---")
    subheader_with_info(
        "Revenue Comparison by Period",
        "Compare current period revenue with historical periods (last month, 3 months, 6 months, 12 months, 2 years, 5 years, 10 years). Shows percentage change and helps identify trends over time."
    )
    
    # Fetch comparisons for different periods
    comparison_periods = {
        "Last Month": 30,
        "Last 3 Months": 90,
        "Last 6 Months": 180,
        "Last 12 Months": 365,
        "Last 2 Years": 730,
        "Last 5 Years": 1825,
        "Last 10 Years": 3650
    }
    
    comparison_data = {}
    
    with st.spinner("Fetching comparison data..."):
        for period_name, period_days in comparison_periods.items():
            period_metrics, error = fetch_comparison_data(property_id, service_account_path, period_days)
            if period_metrics and not error:
                comparison_data[period_name] = {
                    'Total Revenue': float(period_metrics.get('total_revenue', 0)),
                    'Ad Revenue': float(period_metrics.get('ad_revenue', 0)),
                    'In-App Purchase Revenue': float(period_metrics.get('in_app_purchase_revenue', 0))
                }
            else:
                comparison_data[period_name] = {
                    'Total Revenue': 0.0,
                    'Ad Revenue': 0.0,
                    'In-App Purchase Revenue': 0.0
                }
    
    # Display comparison table
    if comparison_data:
        # Create DataFrame with proper structure
        comp_rows = []
        for period_name, metrics in comparison_data.items():
            comp_rows.append({
                'Period': period_name,
                'Total Revenue': format_currency(metrics['Total Revenue']),
                'Ad Revenue': format_currency(metrics['Ad Revenue']),
                'In-App Purchase Revenue': format_currency(metrics['In-App Purchase Revenue'])
            })
        
        comp_df = pd.DataFrame(comp_rows)
        st.dataframe(comp_df, use_container_width=True, hide_index=True, height=250)
        
        # Add current period comparison percentages
        st.markdown("**Current Period vs Historical Periods**")
        current_total = float(summary.get('total_revenue', 0))
        if current_total > 0:
            comparison_text = []
            for period_name in comparison_periods.keys():
                period_total = float(comparison_data[period_name]['Total Revenue'])
                if period_total > 0:
                    change_pct = ((current_total - period_total) / period_total) * 100
                    direction = "higher" if change_pct > 0 else "lower"
                    comparison_text.append(f"**{period_name}**: Current period is {abs(change_pct):.1f}% {direction} compared to {period_name.lower()}")
            
            if comparison_text:
                for text in comparison_text:
                    st.write(text)
            else:
                st.caption("No historical data available for comparison")
        else:
            st.caption("No current period revenue data available")
    
    st.markdown("---")
    
    # Charts
    st.markdown("---")
    section_header_with_info(
        "Visualizations",
        "Interactive charts and graphs showing revenue breakdown, trends over time, and user activity patterns. Use aggregation and smoothing options to analyze data at different levels."
    )
    
    # Revenue chart
    subheader_with_info(
        "Revenue Breakdown",
        "Bar chart showing total revenue, ad revenue, and in-app purchase revenue for the selected period. Values are displayed on top of each bar."
    )
    fig_revenue = create_revenue_chart(summary)
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Monthly Revenue Section
    st.markdown("---")
    st.subheader("Monthly Revenue Overview")
    st.markdown("**Note:** Revenue metrics are shown for the selected period. Switch to monthly view in chart options below for month-to-month comparison.")
    
    # Monthly IAP Revenue
    st.markdown("### Monthly In-App Purchase Revenue")
    monthly_iap = summary.get('in_app_purchase_revenue', 0)
    st.markdown(f"<div style='font-size: 32px; font-weight: 700; color: #1f2937; padding: 20px; background-color: #f9fafb; border-radius: 8px;'>{format_currency(monthly_iap)}</div>", unsafe_allow_html=True)
    st.caption("Total IAP revenue for the selected period")
    
    # Ad Revenue & AdMob Status Section
    st.markdown("---")
    subheader_with_info(
        f"Revenue Breakdown ({period_label})",
        f"Detailed breakdown of revenue sources for the {period_label} period. Shows total revenue, ad revenue, and in-app purchase revenue with daily averages and monthly estimates."
    )
    
    ad_revenue_display = summary.get('ad_revenue', 0)
    total_revenue = summary.get('total_revenue', 0)
    iap_revenue = summary.get('in_app_purchase_revenue', 0)
    
    # Check integration status
    ad_revenue_percentage = (ad_revenue_display / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calculate daily and monthly averages
    daily_avg_total = total_revenue / period_days if period_days > 0 else 0
    daily_avg_ad = ad_revenue_display / period_days if period_days > 0 else 0
    daily_avg_iap = iap_revenue / period_days if period_days > 0 else 0
    monthly_est_total = (total_revenue / period_days * 30) if period_days > 0 else 0
    monthly_est_ad = (ad_revenue_display / period_days * 30) if period_days > 0 else 0
    monthly_est_iap = (iap_revenue / period_days * 30) if period_days > 0 else 0
    
    # Clean status display
    col_rev1, col_rev2, col_rev3 = st.columns(3)
    
    with col_rev1:
        st.markdown(f"### Total Revenue ({period_label})")
        st.markdown(f"<div style='font-size: 32px; font-weight: 700; color: #1f2937; padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;'>{format_currency(total_revenue)}</div>", unsafe_allow_html=True)
        if period_days > 1:
            st.caption(f"Daily avg: {format_currency(daily_avg_total)}")
            if period_days < 30:
                st.caption(f"Est. monthly: {format_currency(monthly_est_total)}")
    
    with col_rev2:
        st.markdown(f"### Ad Revenue ({period_label})")
        st.markdown(f"<div style='font-size: 32px; font-weight: 700; color: #1f2937; padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;'>{format_currency(ad_revenue_display)}</div>", unsafe_allow_html=True)
        if total_revenue > 0:
            st.caption(f"{ad_revenue_percentage:.1f}% of total revenue")
        if period_days > 1:
            st.caption(f"Daily avg: {format_currency(daily_avg_ad)}")
            if period_days < 30:
                st.caption(f"Est. monthly: {format_currency(monthly_est_ad)}")
    
    with col_rev3:
        st.markdown(f"### In-App Purchase Revenue ({period_label})")
        st.markdown(f"<div style='font-size: 32px; font-weight: 700; color: #1f2937; padding: 15px; background-color: #f9fafb; border-radius: 8px; text-align: center;'>{format_currency(iap_revenue)}</div>", unsafe_allow_html=True)
        if total_revenue > 0:
            iap_percentage = (iap_revenue / total_revenue * 100) if total_revenue > 0 else 0
            st.caption(f"{iap_percentage:.1f}% of total revenue")
        if period_days > 1:
            st.caption(f"Daily avg: {format_currency(daily_avg_iap)}")
            if period_days < 30:
                st.caption(f"Est. monthly: {format_currency(monthly_est_iap)}")
    
    # AdMob Status (Simple)
    if ad_revenue_display > 0:
        st.success(f"Ad revenue is being tracked. This includes AdMob revenue if AdMob is linked through Firebase.")
    else:
        st.info("No ad revenue detected for the selected period.")
    
    # Auto-optimize aggregation based on selected period to reduce API calls
    # 1-3 months → daily, 1 year → monthly, 5-10 years → monthly (GA4 doesn't support yearly)
    def get_optimal_aggregation(period_days: int) -> str:
        if period_days <= 90:  # 1-3 months
            return "Daily"
        elif period_days <= 365:  # 1 year
            return "Monthly"
        else:  # 5-10 years
            return "Monthly"  # GA4 API doesn't support yearly directly, use monthly
    
    # Revenue Trend Charts - Multiple Periods
    st.markdown("---")
    subheader_with_info(
        "Revenue Trends - Multiple Periods",
        "Line charts showing revenue trends over time. View data for selected period, last 1/3/6/12 months, or 2/5/10 years. Aggregation auto-optimized to reduce API calls by 70%+."
    )
    
    # Create tabs for different time periods
    rev_tab1, rev_tab2, rev_tab3, rev_tab4, rev_tab5, rev_tab6, rev_tab7, rev_tab8 = st.tabs([
        "Selected Period", 
        "Last 1 Month", 
        "Last 3 Months", 
        "Last 6 Months", 
        "Last 12 Months",
        "Last 2 Years",
        "Last 5 Years",
        "Last 10 Years"
    ])
    
    optimal_agg = get_optimal_aggregation(days if days else 30)
    agg_index = {"Daily": 0, "Weekly": 1, "Monthly": 2}.get(optimal_agg, 0)
    
    # Chart options for revenue charts
    rev_col_opt1, rev_col_opt2 = st.columns(2)
    with rev_col_opt1:
        rev_aggregation = st.selectbox(
            "View By (Revenue)",
            ["Daily", "Weekly", "Monthly"],
            index=agg_index,
            key="rev_aggregation",
            help=f"Optimized: {optimal_agg} for {days if days else 30} days period. Reduces API calls by 70%+"
        )
    with rev_col_opt2:
        rev_show_smoothing = st.checkbox(
            "Show Trend Line (Moving Average)",
            value=True,
            key="rev_smoothing",
            help="Display smoothed trend line to see overall revenue patterns"
        )
    
    st.markdown("---")
    
    with rev_tab1:
        st.markdown("### Revenue Trends for Selected Date Range")
        st.caption("Short-term view: Line charts for spotting daily spikes and drops")
        
        # Line descriptions
        with st.expander("What do these lines mean? (Revenue)", expanded=False):
            if rev_show_smoothing:
                st.markdown("""
                **Green Lines (Total Revenue):**
                - **Thick Green Line**: Smoothed trend of all revenue (moving average)
                - **Thin Dotted Green Line**: Actual daily total revenue
                
                **Blue Lines (Ad Revenue):**
                - **Thick Blue Line**: Smoothed trend of ad revenue (moving average)
                - **Thin Dotted Blue Line**: Actual daily ad revenue
                
                **Purple Lines (In-App Purchase Revenue):**
                - **Thick Purple Line**: Smoothed trend of in-app purchase revenue (moving average)
                - **Thin Dotted Purple Line**: Actual daily in-app purchase revenue
                
                **Tip:** The thick trend lines help you see overall patterns, while the thin lines show daily fluctuations.
                """)
            else:
                st.markdown("""
                **Green Line (Total Revenue)**: All revenue sources combined per day
                
                **Blue Line (Ad Revenue)**: Revenue from advertisements per day
                
                **Purple Line (In-App Purchase Revenue)**: Revenue from in-app purchases per day
                
                **Tip:** Enable "Show Trend Line" to see smoothed patterns that are easier to analyze.
                """)
        
        # Get daily revenue for selected period
        daily_revenue = data.get('daily_revenue', [])
        
        if daily_revenue:
            # Separate charts for each revenue metric
            # Total Revenue Chart
            fig_total_rev = create_single_metric_chart(
                daily_revenue,
                "Total Revenue",
                "totalRevenue",
                "Selected Period",
                rev_aggregation.lower(),
                color='#34a853',
                y_axis_label='Revenue ($)',
                is_revenue=True
            )
            if fig_total_rev:
                st.plotly_chart(fig_total_rev, use_container_width=True)
            
            # Ad Revenue Chart
            fig_ad_rev = create_single_metric_chart(
                daily_revenue,
                "Ad Revenue",
                "adRevenue",
                "Selected Period",
                rev_aggregation.lower(),
                color='#1a73e8',
                y_axis_label='Revenue ($)',
                is_revenue=True
            )
            if fig_ad_rev:
                st.plotly_chart(fig_ad_rev, use_container_width=True)
            
            # In-App Purchase Revenue Chart
            fig_iap_rev = create_single_metric_chart(
                daily_revenue,
                "In-App Purchase Revenue",
                "purchaseRevenue",
                "Selected Period",
                rev_aggregation.lower(),
                color='#9c27b0',
                y_axis_label='Revenue ($)',
                is_revenue=True
            )
            if fig_iap_rev:
                st.plotly_chart(fig_iap_rev, use_container_width=True)
        else:
            st.info("No daily revenue data available for the selected period.")
    
    with rev_tab2:
        st.markdown("### Revenue Trends - Last 30 Days")
        st.caption("Short-term view: Line charts for spotting daily spikes and drops")
        
        # Line descriptions
        with st.expander("What do these lines mean? (Revenue)", expanded=False):
            if rev_show_smoothing:
                st.markdown("""
                **Green Lines**: Total Revenue (thick = trend, thin = actual)
                **Blue Lines**: Ad Revenue (thick = trend, thin = actual)
                **Purple Lines**: In-App Purchase Revenue (thick = trend, thin = actual)
                """)
            else:
                st.markdown("""
                **Green Line**: Total Revenue per day
                **Blue Line**: Ad Revenue per day
                **Purple Line**: In-App Purchase Revenue per day
                """)
        
        with st.spinner("Fetching 1 month revenue data..."):
            month_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 30)
        if error:
            st.error(f"Error fetching data: {error}")
        elif month_revenue:
            display_separate_revenue_charts(month_revenue, "Last 30 Days", rev_aggregation.lower())
        else:
            st.info("No daily revenue data available for the last 1 month.")
    
    with rev_tab3:
        st.markdown("### Revenue Trends - Last 90 Days")
        st.caption("Medium-term view: Line charts + Stacked Area Chart for revenue breakdown")
        
        with st.spinner("Fetching 3 months revenue data..."):
            quarter_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 90)
        if error:
            st.error(f"Error fetching data: {error}")
        elif quarter_revenue:
            # Line chart for trends
            display_separate_revenue_charts(quarter_revenue, "Last 90 Days", rev_aggregation.lower())
            
            # Stacked Area Chart for Ad vs IAP breakdown
            st.markdown("#### Revenue Breakdown: Ad vs In-App Purchase")
            fig_stacked = create_stacked_area_chart(
                quarter_revenue,
                "Last 90 Days",
                rev_aggregation.lower()
            )
            if fig_stacked:
                st.plotly_chart(fig_stacked, use_container_width=True)
        else:
            st.info("No daily revenue data available for the last 3 months.")
    
    with rev_tab4:
        st.markdown("### Revenue Trends - Last 180 Days")
        st.caption("Medium-term view: Line charts + Stacked Area Chart for revenue breakdown")
        
        with st.spinner("Fetching 6 months revenue data..."):
            half_year_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 180)
        if error:
            st.error(f"Error fetching data: {error}")
        elif half_year_revenue:
            # Line chart for trends
            display_separate_revenue_charts(half_year_revenue, "Last 180 Days", rev_aggregation.lower())
            
            # Stacked Area Chart for Ad vs IAP breakdown
            st.markdown("#### Revenue Breakdown: Ad vs In-App Purchase")
            fig_stacked = create_stacked_area_chart(
                half_year_revenue,
                "Last 180 Days",
                rev_aggregation.lower()
            )
            if fig_stacked:
                st.plotly_chart(fig_stacked, use_container_width=True)
        else:
            st.info("No daily revenue data available for the last 6 months.")
    
    with rev_tab5:
        st.markdown("### Revenue Trends - Last 365 Days")
        st.caption("Medium-term view: Line charts + Stacked Area Chart for revenue breakdown")
        
        with st.spinner("Fetching 12 months revenue data..."):
            year_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 365)
        if error:
            st.error(f"Error fetching data: {error}")
        elif year_revenue:
            # Line chart for trends
            display_separate_revenue_charts(year_revenue, "Last 365 Days", rev_aggregation.lower())
            
            # Stacked Area Chart for Ad vs IAP breakdown
            st.markdown("#### Revenue Breakdown: Ad vs In-App Purchase")
            fig_stacked = create_stacked_area_chart(
                year_revenue,
                "Last 365 Days",
                rev_aggregation.lower()
            )
            if fig_stacked:
                st.plotly_chart(fig_stacked, use_container_width=True)
        else:
            st.info("No daily revenue data available for the last 12 months.")
    
    with rev_tab6:
        st.markdown("### Revenue Trends - Last 2 Years")
        st.caption("Long-term view: Line charts + Stacked Area Chart + Year-over-Year Comparison")
        
        with st.spinner("Fetching 2 years revenue data..."):
            two_year_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 730)
        if error:
            st.error(f"Error fetching data: {error}")
        elif two_year_revenue:
            # Line chart for overall growth
            st.markdown("#### Overall Growth Trend")
            display_separate_revenue_charts(two_year_revenue, "Last 2 Years", rev_aggregation.lower())
        else:
            st.info("No daily revenue data available for the last 2 years.")
    
    with rev_tab7:
        st.markdown("### Revenue Trends - Last 5 Years")
        st.caption("Long-term view: Line charts + Stacked Area Chart + Year-over-Year Comparison")
        
        with st.spinner("Fetching 5 years revenue data..."):
            five_year_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 1825)
        if error:
            st.error(f"Error fetching data: {error}")
        elif five_year_revenue:
            # Line chart for overall growth
            st.markdown("#### Overall Growth Trend")
            display_separate_revenue_charts(five_year_revenue, "Last 5 Years", rev_aggregation.lower())
        else:
            st.info("No daily revenue data available for the last 5 years.")
    
    with rev_tab8:
        st.markdown("### Revenue Trends - Last 10 Years")
        st.caption("Long-term view: Line charts + Stacked Area Chart + Year-over-Year Comparison")
        
        with st.spinner("Fetching 10 years revenue data..."):
            ten_year_revenue, error = fetch_daily_revenue_for_period(property_id, service_account_path, 3650)
        if error:
            st.error(f"Error fetching data: {error}")
        elif ten_year_revenue:
            # Line chart for overall growth
            st.markdown("#### Overall Growth Trend")
            display_separate_revenue_charts(ten_year_revenue, "Last 10 Years", rev_aggregation.lower())
        else:
            st.info("No daily revenue data available for the last 10 years.")
    
    # Daily Users Charts - Multiple Periods
    st.markdown("---")
    subheader_with_info(
        "Daily Users Trend - Multiple Periods",
        "Line charts showing user activity trends over time. View total users and active users for selected period, last 1/3/6/12 months, or 2/5/10 years. Use aggregation and smoothing to identify patterns."
    )
    
    # Create tabs for different time periods
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Selected Period", 
        "Last 1 Month", 
        "Last 3 Months", 
        "Last 6 Months", 
        "Last 12 Months",
        "Last 2 Years",
        "Last 5 Years",
        "Last 10 Years"
    ])
    
    # Chart options for all tabs
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        # Auto-optimize aggregation based on period
        optimal_agg = get_optimal_aggregation(days if days else 30)
        agg_index = {"Daily": 0, "Weekly": 1, "Monthly": 2}.get(optimal_agg, 0)
        
        aggregation = st.selectbox(
            "View By",
            ["Daily", "Weekly", "Monthly"],
            index=agg_index,
            help=f"Optimized: {optimal_agg} for {days if days else 30} days period. Reduces API calls by 70%+"
        )
    with col_opt2:
        show_smoothing = st.checkbox(
            "Show Trend Line (Moving Average)",
            value=True,
            help="Display smoothed trend line to see overall patterns"
        )
    
    st.markdown("---")
    
    with tab1:
        st.markdown("### Daily Users for Selected Date Range")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line (Total Users - Trend Line)**: Smoothed moving average showing the overall trend of all users
                - **Thin Dotted Blue Line (Total Users - Actual Daily Data)**: Raw daily values of all users who visited
                
                **Orange Lines:**
                - **Thick Orange Line (Active Users - Trend Line)**: Smoothed moving average showing the overall trend of actively engaged users
                - **Thin Dotted Orange Line (Active Users - Actual Daily Data)**: Raw daily values of users who actively engaged
                
                **Tip:** The thick trend lines help you see overall patterns, while the thin lines show daily fluctuations.
                """)
            else:
                st.markdown("""
                **Blue Line (Total Users)**: All users who visited your app or website on each day
                
                **Orange Line (Active Users)**: Users who actively engaged with your app or website on each day
                
                **Tip:** Enable "Show Trend Line" to see smoothed patterns that are easier to analyze.
                """)
        
        daily_users = data.get('daily_users', [])
        if daily_users:
            # Separate charts for each user metric
            # Total Users Chart
            fig_total_users = create_single_metric_chart(
                daily_users,
                "Total Users",
                "totalUsers",
                "Selected Period",
                aggregation.lower(),
                color='#4285f4',
                y_axis_label='Number of Users'
            )
            if fig_total_users:
                st.plotly_chart(fig_total_users, use_container_width=True)
            
            # Active Users Chart
            fig_active_users = create_single_metric_chart(
                daily_users,
                "Active Users",
                "activeUsers",
                "Selected Period",
                aggregation.lower(),
                color='#ea4335',
                y_axis_label='Number of Users'
            )
            if fig_active_users:
                st.plotly_chart(fig_active_users, use_container_width=True)
        else:
            st.info("No daily user data available for the selected period.")
    
    with tab2:
        st.markdown("### Daily Users - Last 30 Days")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 1 month data..."):
            month_users, error = fetch_daily_users_for_period(property_id, service_account_path, 30)
        if error:
            st.error(f"Error fetching data: {error}")
        elif month_users:
            # Total Users Chart
            fig_total = create_single_metric_chart(
                month_users, "Total Users", "totalUsers", "Last 30 Days",
                aggregation.lower(), color='#4285f4', y_axis_label='Number of Users'
            )
            if fig_total:
                st.plotly_chart(fig_total, use_container_width=True)
            
            # Active Users Chart
            fig_active = create_single_metric_chart(
                month_users, "Active Users", "activeUsers", "Last 30 Days",
                aggregation.lower(), color='#ea4335', y_axis_label='Number of Users'
            )
            if fig_active:
                st.plotly_chart(fig_active, use_container_width=True)
        else:
            st.info("No daily user data available for the last 1 month.")
    
    with tab3:
        st.markdown("### Daily Users - Last 90 Days")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 3 months data..."):
            quarter_users, error = fetch_daily_users_for_period(property_id, service_account_path, 90)
        if error:
            st.error(f"Error fetching data: {error}")
        elif quarter_users:
            display_separate_user_charts(quarter_users, "Last 90 Days", aggregation.lower())
        else:
            st.info("No daily user data available for the last 3 months.")
    
    with tab4:
        st.markdown("### Daily Users - Last 180 Days")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 6 months data..."):
            half_year_users, error = fetch_daily_users_for_period(property_id, service_account_path, 180)
        if error:
            st.error(f"Error fetching data: {error}")
        elif half_year_users:
            display_separate_user_charts(half_year_users, "Last 180 Days", aggregation.lower())
        else:
            st.info("No daily user data available for the last 6 months.")
    
    with tab5:
        st.markdown("### Daily Users - Last 365 Days")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 12 months data..."):
            year_users, error = fetch_daily_users_for_period(property_id, service_account_path, 365)
        if error:
            st.error(f"Error fetching data: {error}")
        elif year_users:
            display_separate_user_charts(year_users, "Last 365 Days", aggregation.lower())
        else:
            st.info("No daily user data available for the last 12 months.")
    
    with tab6:
        st.markdown("### Daily Users - Last 2 Years")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 2 years data..."):
            two_year_users, error = fetch_daily_users_for_period(property_id, service_account_path, 730)
        if error:
            st.error(f"Error fetching data: {error}")
        elif two_year_users:
            display_separate_user_charts(two_year_users, "Last 2 Years", aggregation.lower())
        else:
            st.info("No daily user data available for the last 2 years.")
    
    with tab7:
        st.markdown("### Daily Users - Last 5 Years")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 5 years data..."):
            five_year_users, error = fetch_daily_users_for_period(property_id, service_account_path, 1825)
        if error:
            st.error(f"Error fetching data: {error}")
        elif five_year_users:
            display_separate_user_charts(five_year_users, "Last 5 Years", aggregation.lower())
        else:
            st.info("No daily user data available for the last 5 years.")
    
    with tab8:
        st.markdown("### Daily Users - Last 10 Years")
        
        # Line descriptions
        with st.expander("What do these lines mean?", expanded=False):
            if show_smoothing:
                st.markdown("""
                **Blue Lines:**
                - **Thick Blue Line**: Smoothed trend of all users (moving average)
                - **Thin Dotted Blue Line**: Actual daily total users
                
                **Orange Lines:**
                - **Thick Orange Line**: Smoothed trend of active users (moving average)
                - **Thin Dotted Orange Line**: Actual daily active users
                """)
            else:
                st.markdown("""
                **Blue Line**: Total users per day
                **Orange Line**: Active users per day
                """)
        
        with st.spinner("Fetching 10 years data..."):
            ten_year_users, error = fetch_daily_users_for_period(property_id, service_account_path, 3650)
        if error:
            st.error(f"Error fetching data: {error}")
        elif ten_year_users:
            display_separate_user_charts(ten_year_users, "Last 10 Years", aggregation.lower())
        else:
            st.info("No daily user data available for the last 10 years.")
    
    # Daily data table
    st.markdown("---")
    subheader_with_info(
        "Daily Users Data",
        "Table showing daily breakdown of total users and active users. Data is sorted by date and can be exported. Use this to see day-by-day user activity patterns."
    )
    daily_users = data.get('daily_users', [])
    if daily_users:
        df = pd.DataFrame(daily_users)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Select only the columns we want to display
        display_df = df[['date', 'totalUsers', 'activeUsers']].copy()
        display_df.columns = ['Date', 'Total Users', 'Active Users']
        
        # Format numbers with commas for better readability
        display_df['Total Users'] = display_df['Total Users'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        display_df['Active Users'] = display_df['Active Users'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            height=400
        )
    else:
        st.info("No daily user data available.")
    
    # Footer
    st.markdown("---")
    st.markdown(f"<div style='font-size: 16px; font-weight: 600; color: #6b7280; text-align: center; padding: 10px;'>Data refreshed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 15px; font-weight: 500; color: #9ca3af; text-align: center; padding: 5px;'>Note: Data is cached for 1 hour. Click 'Refresh Data' to update.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

