import pandas as pd
from prophet import Prophet
import logging

# Suppress Prophet logs
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

def predict_prophet(df: pd.DataFrame, days_forecast: int = 7):
    """
    Uses Facebook Prophet for forecasting.
    Requires columns renamed to 'ds' and 'y'.
    """
    # Prepare Data
    prophet_df = df[['date', 'close']].copy()
    prophet_df.columns = ['ds', 'y']
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds']).dt.tz_localize(None) # Remove timezone if present

    # Train
    m = Prophet(daily_seasonality=True)
    m.fit(prophet_df)

    # Create Future Dataframe
    future = m.make_future_dataframe(periods=days_forecast)
    
    # Predict
    forecast = m.predict(future)
    
    # Extract only the future predictions
    future_predictions = forecast.tail(days_forecast)['yhat'].values.tolist()
    
    return future_predictions