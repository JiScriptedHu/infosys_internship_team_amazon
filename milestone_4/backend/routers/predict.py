from fastapi import APIRouter, HTTPException, Query
import os
import sys

# 1. Suppress TensorFlow Info/Warning logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import yfinance as yf
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import traceback

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Suppress Prophet Plotly Error
logging.getLogger("prophet.plot").setLevel(logging.CRITICAL)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

# 3. Model Registry & Availability Check
MODELS = {
    "lstm": {"func": None, "error": None},
    "xgboost": {"func": None, "error": None},
    "prophet": {"func": None, "error": None},
    "arima": {"func": None, "error": None},
    "tft": {"func": None, "error": None},
}

# Import Models gracefully
try:
    from models.lstm_model import predict_lstm
    MODELS["lstm"]["func"] = predict_lstm
except ImportError as e:
    MODELS["lstm"]["error"] = "TensorFlow/Keras not installed"
    logger.warning(f"LSTM unavailable: {e}")

try:
    from models.xgboost_model import predict_xgboost
    MODELS["xgboost"]["func"] = predict_xgboost
except ImportError as e:
    MODELS["xgboost"]["error"] = "XGBoost not installed"
    logger.warning(f"XGBoost unavailable: {e}")

try:
    from models.prophet_model import predict_prophet
    MODELS["prophet"]["func"] = predict_prophet
except ImportError as e:
    MODELS["prophet"]["error"] = "Prophet not installed"
    logger.warning(f"Prophet unavailable: {e}")

try:
    from models.arima_model import predict_arima
    MODELS["arima"]["func"] = predict_arima
except ImportError as e:
    MODELS["arima"]["error"] = "Statsmodels/ARIMA not installed"
    logger.warning(f"ARIMA unavailable: {e}")

try:
    from models.tft_model import predict_tft
    MODELS["tft"]["func"] = predict_tft
except ImportError as e:
    MODELS["tft"]["error"] = "PyTorch not installed"
    logger.warning(f"TFT unavailable: {e}")


router = APIRouter()
executor = ThreadPoolExecutor(max_workers=3)

def fetch_historical_data(ticker: str):
    """
    Fetches 2 years of historical data for model training.
    """
    try:
        logger.info(f"Fetching training data for {ticker}...")
        stock = yf.Ticker(ticker)
        # Fetch 2y to ensure enough data. auto_adjust=True matches market.py logic.
        hist = stock.history(period="2y", auto_adjust=True)
        
        if hist.empty:
            logger.warning(f"No data found for {ticker}")
            return pd.DataFrame()

        # Clean Data
        hist.reset_index(inplace=True)
        
        # Ensure Date column is string format YYYY-MM-DD
        if 'Date' in hist.columns:
            hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
            
        # Standardize column names to lowercase
        hist.columns = [c.lower() for c in hist.columns]
        
        # Ensure we have date and close
        if 'date' not in hist.columns or 'close' not in hist.columns:
            return pd.DataFrame()

        return hist[['date', 'close']]
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def run_model(model_name: str, df: pd.DataFrame, days: int):
    """
    Routes to the correct model function.
    """
    model_info = MODELS.get(model_name)
    
    # 1. Check if model exists and is installed
    if not model_info:
        raise ValueError("Invalid model name")
    
    if model_info["func"] is None:
        raise ImportError(model_info["error"] or "Model library missing")

    # 2. Check Data Sufficiency
    if df.empty or len(df) < 60:
        raise ValueError("Insufficient historical data (need 60+ days)")

    # 3. Run Prediction
    try:
        logger.info(f"Running {model_name} for {days} days...")
        predictions = model_info["func"](df, days)
        return predictions
    except Exception as e:
        logger.error(f"Runtime error in {model_name}: {e}")
        traceback.print_exc()
        raise RuntimeError(f"Model execution failed: {str(e)}")

@router.get("/{model_name}/{ticker}")
async def get_prediction(model_name: str, ticker: str, days: int = 7):
    model_name = model_name.lower()
    if model_name not in MODELS:
        raise HTTPException(status_code=400, detail="Invalid model name")
    
    try:
        loop = asyncio.get_event_loop()
        
        # 1. Fetch Data
        df = await loop.run_in_executor(executor, fetch_historical_data, ticker)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")

        # 2. Run Prediction (Wrapped to catch internal errors)
        try:
            predictions = await loop.run_in_executor(executor, run_model, model_name, df, days)
        except ImportError as ie:
            raise HTTPException(status_code=501, detail=str(ie)) # Not Implemented / Missing Lib
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except RuntimeError as re:
            raise HTTPException(status_code=500, detail=str(re))
        
        if not predictions:
            raise HTTPException(status_code=500, detail=f"{model_name} returned no predictions.")
        
        return {
            "model": model_name,
            "ticker": ticker.upper(),
            "forecast": predictions
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))