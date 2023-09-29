import pandas as pd
import pytz
from datetime import datetime, timedelta
import re


# Initialize the auto suspend minutes
auto_suspend_minutes = 10

def process_csv(file_name):
    df = pd.read_csv(file_name, parse_dates=['TimeGenerated [UTC]'])

    # Sort DataFrame by 'TimeGenerated [UTC]'
    df.sort_values(by='TimeGenerated [UTC]', inplace=True, ascending=True)

    # Set timezone to UTC for conversions later
    tz = pytz.timezone('America/Chicago')
    df['TimeGenerated [UTC]'] = df['TimeGenerated [UTC]'].dt.tz_localize(tz)

    windows_data = []
    current_window_start = df.iloc[0]['TimeGenerated [UTC]']
    current_window_end = current_window_start + timedelta(minutes=auto_suspend_minutes)
    current_running_start = None
    current_running_end = None
    total_queries = 0
    distinct_queries_cache = set()
    cached_queries = 0
    for index, row in df.iterrows():
        query_time = row['TimeGenerated [UTC]']
        query_statement = str(row['statement_s']).strip().upper()

        if (query_time > current_window_end):
            # Store the current window's data
            windows_data.append({
                'Day': current_window_start.date(),
                'window_start': current_window_start.strftime('%m/%d/%Y %I:%M %p %Z'),
                'window_end': current_window_end.strftime('%m/%d/%Y %I:%M %p %Z'),
                'total_queries': total_queries,
                'distinct_queries': total_queries - cached_queries,
                'cached_queries': cached_queries,
                'running_start': '' if current_running_start is None else current_running_start.strftime('%m/%d/%Y %I:%M %p %Z'),
                'running_end': '' if current_running_end is None else current_running_end.strftime('%m/%d/%Y %I:%M %p %Z'),
                'running_minutes': 0 if current_running_start is None or current_running_end is None else round((current_running_end - current_running_start).seconds / 60, 2)
            })

            # Reset counters and start a new window
            total_queries = 0
            cached_queries = 0
            current_running_start = None
            current_running_end = None
            current_window_start = query_time

        current_window_end = query_time + timedelta(minutes=auto_suspend_minutes)

        # Reset cache if TRUNCATE, INSERT, or UPDATE statement
        if re.search(r'\bTRUNCATE\b', query_statement) or re.search(r'\bINSERT\b', query_statement) or re.search(r'\bUPDATE\b', query_statement):
            distinct_queries_cache.clear()

        # Counting queries
        total_queries += 1
        if query_statement not in distinct_queries_cache:
            distinct_queries_cache.add(query_statement)
            if current_running_start == None:
                current_running_start = query_time
            current_running_end = query_time + timedelta(minutes=auto_suspend_minutes)
        else:
            cached_queries += 1

     # Add the last window if it exists
    if total_queries > 0:
        windows_data.append({
            'Day': current_window_start.date(),
            'window_start': current_window_start.strftime('%m/%d/%Y %I:%M %p %Z'),
            'window_end': current_window_end.strftime('%m/%d/%Y %I:%M %p %Z'),
            'total_queries': total_queries,
            'distinct_queries': total_queries - cached_queries,
            'cached_queries': len(distinct_queries_cache),
            'running_start': '' if current_running_start is None else current_running_start.strftime('%m/%d/%Y %I:%M %p %Z'),
            'running_end': '' if current_running_end is None else current_running_end.strftime('%m/%d/%Y %I:%M %p %Z'),
            'running_minutes': 0 if current_running_start is None or current_running_end is None else round((current_running_end - current_running_start).seconds / 60, 2),
        })

    # Convert the results list to DataFrame and save to Excel
    results_df = pd.DataFrame(windows_data)

    # Daily
    daily_agg = results_df.groupby('Day').agg({
        'total_queries': 'sum',
        'distinct_queries': 'sum',
        'cached_queries':'sum',
        'running_minutes': 'sum'
    }).reset_index()

    # Save the results to a new file with two worksheets
    with pd.ExcelWriter('query_data_analysis.xlsx') as writer:
        results_df.to_excel(writer, sheet_name='warehouse_utiliztion', index=False)
        daily_agg.reset_index().to_excel(writer, sheet_name='daily_aggregation', index=False)

# Execute
process_csv('query_data.csv')
