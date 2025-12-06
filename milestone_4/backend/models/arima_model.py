import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import warnings

def predict_arima(df: pd.DataFrame, days_forecast: int = 7):
    """
    Uses ARIMA (AutoRegressive Integrated Moving Average).
    """
    warnings.filterwarnings("ignore")
    
    data = df['close'].values
    
    # Simple fixed order (5,1,0) for speed/stability in demo
    # In production, use pmdarima.auto_arima to find best order
    try:
        model = ARIMA(data, order=(5, 1, 0))
        model_fit = model.fit()
        
        output = model_fit.forecast(steps=days_forecast)
        return output.tolist()
    except Exception as e:
        print(f"ARIMA Error: {e}")
        return []