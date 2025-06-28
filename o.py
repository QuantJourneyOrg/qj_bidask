from quantjourney_bidask import edge_rolling
import pandas as pd

# Create a sample DataFrame with at least 3 rows of OHLC data
df = pd.DataFrame({
    'open': [100.0, 101.0, 100.5, 102.0],
    'high': [102.0, 103.0, 101.5, 103.5],
    'low': [99.0, 100.0, 99.5, 101.0],
    'close': [101.0, 102.0, 101.0, 102.5]
})

# Calculate spreads using edge_rolling with a valid window size
spreads = edge_rolling(df, window=3)
print(spreads)
