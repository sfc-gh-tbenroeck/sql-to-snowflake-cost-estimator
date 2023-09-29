# Snowflake Cost Estimator Script

This script processes a history of SQL query data to estimate the potential cost of running these queries on Snowflake, taking into consideration features like caching and warehouse auto-suspend.

## Table of Contents
1. [Getting the Query Log](#getting-the-query-log)
2. [How to Use the Script](#how-to-use-the-script)
3. [Notes](#notes)
4. [Logic](#logic)

## Getting the Query Log

There are two methods to get the SQL query log depending on your setup:

### 1. Auditing for Azure SQL Database and Azure Synapse Analytics

Follow the steps from the official Microsoft documentation to set up Auditing for Azure SQL Database and Azure Synapse Analytics. Here's the [link to the guide](https://learn.microsoft.com/en-us/azure/azure-sql/database/auditing-setup?view=azuresql).

**Note**: If your database is hosted in Azure, it's more straightforward to use Azure Audit Logs. However, ensure that you log them to a Log Analytics workspace instead of a Storage Account. This is because the storage account log file is a binary file and must be opened in SQL Server.

### 2. SQL's Query Store

If you're using SQL's Query Store for logging, follow the steps from the official Microsoft documentation. Here's the [link to the guide](https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store?view=sql-server-ver16).

**Note**: The Query Store has the capability to log all queries, but it doesn't do so by default.

## How to Use the Script

1. **Prerequisites**: Ensure you have Python and the required libraries installed
```python
pip install pandas openpyxl pytz
```

2. **Input Data**: Have your query log ready in a CSV format. This script is designed to process a file named `query_data.csv`. Ensure your CSV file contains columns for `TimeGenerated [UTC]` and `statement_s`.

3. **Run the Script**: Execute the Python script either via command line or an IDE of your choice.

```bash
python query_data_analysis.py
```

4. **Output**: The script will generate an Excel file called `query_data_analysis.xlsx` with two sheets:
   - `warehouse_utilization` - Detailed data for each time window.
   - `daily_aggregation` - Aggregated data for each day.

## Notes

- Make sure your query log captures the full range of data needed for this analysis.
- If using Azure Audit Logs, remember to choose a Log Analytics workspace for your destination to avoid dealing with binary files in Storage Accounts.
- The Query Store doesn't log all queries by default; adjustments might be needed based on your requirements.


## Logic

**Organizing Data**:
   - The data is sorted in chronological order.
   - The code sets up time windows based on the 'auto suspend' feature. Each window is defined as the period between when a query starts until 10 minutes after the last query in that time frame.

**Analyzing Queries**:
   - For each query in the time window, the code checks:
     - If it's a new unique query. If so, it records the time and assumes the warehouse would be active for this.
     - If the query has been executed before within the window. If so, it's a cached query, meaning the warehouse doesn't need to run.
   - If there are any "TRUNCATE" or "INSERT" statements, it assumes the cache gets cleared. This is because such operations might change the data, making previous caches invalid.

**Summarizing Data**:
   - After processing all the queries, the code compiles a summary for each window:
     - When the window started and ended.
     - Total number of queries.
     - Number of distinct (unique) queries.
     - Number of cached queries.
     - Duration the warehouse was actively running.

**Daily Aggregation**:
   - The data is further aggregated on a daily basis. For each day, the code calculates:
     - Total number of queries.
     - Total number of distinct queries.
     - Total number of cached queries.
     - Total active minutes of the warehouse.

**Business Benefit**:
By using this code, you get a clear picture of how your queries would perform on Snowflake. You can see how often a warehouse might be active, how much you can benefit from caching, and ultimately get an estimate of potential costs. This analysis can help in making informed decisions related to budgeting and optimizing query performance.
