import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import tensorflow as tf

# Suppress TF warnings
tf.get_logger().setLevel('ERROR')

def predict_lstm(df: pd.DataFrame, days_forecast: int = 7):
    """
    Trains a simple LSTM on the provided dataframe and forecasts future days.
    Expected df columns: ['date', 'close', ...]
    """
    # 1. Prepare Data
    data = df['close'].values.reshape(-1, 1)
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    # Create sequences
    prediction_days = 60
    x_train, y_train = [], []
    
    if len(scaled_data) <= prediction_days:
        return [] # Not enough data

    for i in range(prediction_days, len(scaled_data)):
        x_train.append(scaled_data[i-prediction_days:i, 0])
        y_train.append(scaled_data[i, 0])
        
    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    # 2. Build Model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dense(units=25))
    model.add(Dense(units=1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    
    # Train (low epochs for demo speed)
    model.fit(x_train, y_train, batch_size=32, epochs=1, verbose=0)

    # 3. Forecast
    future_outputs = []
    last_60_days = scaled_data[-prediction_days:]
    
    current_batch = last_60_days.reshape((1, prediction_days, 1))
    
    for i in range(days_forecast):
        pred_scaled = model.predict(current_batch, verbose=0)[0]
        future_outputs.append(pred_scaled)
        
        # Update batch: remove first, add new prediction
        current_batch = np.append(current_batch[:, 1:, :], [[pred_scaled]], axis=1)

    # Inverse transform
    predictions = scaler.inverse_transform(future_outputs)
    return predictions.flatten().tolist()