import pandas as pd
import numpy as np
from xgboost import XGBRegressor

def predict_xgboost(df: pd.DataFrame, days_forecast: int = 7):
    """
    Trains an XGBoost model using lagged features.
    """
    try:
        df = df.copy()
        
        # Ensure date is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
            
        df = df.set_index('date')
        
        # Create Lag Features (Window Size = 3)
        for i in range(1, 4):
            df[f'lag_{i}'] = df['close'].shift(i)
            
        df = df.dropna()
        
        # Ensure sufficient data exists for training
        if df.empty or len(df) < 10:
            return []

        features = [f'lag_{i}' for i in range(1, 4)]
        target = 'close'
        
        X = df[features]
        y = df[target]
        
        # Train Model
        model = XGBRegressor(objective='reg:squarederror', n_estimators=100)
        model.fit(X, y)
        
        # --- Forecast Loop ---
        # 1. Extract the last known window of data to start predictions
        last_known_row = df.iloc[-1][features]
        current_input_values = last_known_row.values # Array: [lag_1, lag_2, lag_3]
        
        predictions = []
        
        for _ in range(days_forecast):
            # Fix: Convert input to DataFrame with feature names to satisfy XGBoost strict mode
            input_df = pd.DataFrame([current_input_values], columns=features)
            
            # Predict next value
            next_pred = model.predict(input_df)[0]
            
            # Fix: Cast numpy float to python float for JSON serialization
            predictions.append(float(next_pred))
            
            # Shift Window Logic:
            # New Input = [Prediction, Old_Lag_1, Old_Lag_2]
            # (Note: lag_1 is the most recent past value)
            new_input = np.array([next_pred, current_input_values[0], current_input_values[1]])
            current_input_values = new_input
            
        return predictions

    except Exception as e:
        print(f"XGBoost Model Error: {e}")
        return []