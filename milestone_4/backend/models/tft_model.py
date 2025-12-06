import pandas as pd
import numpy as np
import torch
import random
import torch.nn as nn

class SimpleTransformer(nn.Module):
    def __init__(self, feature_size=1, d_model=32, num_layers=2, dropout=0.1):
        super(SimpleTransformer, self).__init__()
        self.d_model = d_model
        
        # 1. Input Projection (Embed features to d_model size)
        self.encoder_input_layer = nn.Linear(feature_size, d_model)
        
        # 2. Positional Encoding (Learnable)
        # Max sequence length 500 is sufficient for our 60-90 day windows
        self.pos_encoder = nn.Parameter(torch.zeros(1, 500, d_model)) 
        
        # 3. Transformer Encoder
        self.encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=4, dim_feedforward=64, dropout=dropout)
        self.transformer_encoder = nn.TransformerEncoder(self.encoder_layer, num_layers=num_layers)
        
        # 4. Output Projection
        self.decoder = nn.Linear(d_model, 1)
        
        self.init_weights()

    def init_weights(self):
        initrange = 0.1
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def _generate_square_subsequent_mask(self, sz):
        # Generates an upper-triangular matrix of -inf, with zeros on diag.
        return torch.triu(torch.full((sz, sz), float('-inf')), diagonal=1)

    def forward(self, src):
        # src shape: (Seq_Len, Batch, Feature)
        
        # Project to d_model
        src = self.encoder_input_layer(src) 
        
        # Add Positional Encoding
        seq_len = src.size(0)
        # Transpose pos_encoder to (Seq, 1, d_model) to match src broadcasting
        src = src + self.pos_encoder[:, :seq_len, :].transpose(0, 1)

        # Generate Causal Mask (Important for time series!)
        mask = self._generate_square_subsequent_mask(seq_len).to(src.device)

        output = self.transformer_encoder(src, mask=mask)
        output = self.decoder(output)
        return output

def predict_tft(df: pd.DataFrame, days_forecast: int = 7):
    """
    Implementation of a basic Transformer for Time Series (TFT proxy).
    Real TFT requires 'pytorch-forecasting' TimeSeriesDataSet setup which is complex for a simple API.
    """
    # 0. Set Seeds for Consistency
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)

    # 1. Data Prep
    data = df['close'].values.astype(float)
    max_val = np.max(data)
    data = data / max_val # Normalize
    
    # Shape: (Seq_Len, Batch=1, Feature=1)
    data_tensor = torch.FloatTensor(data).view(-1, 1, 1) 
    
    # 2. Model (Increased complexity for better learning)
    model = SimpleTransformer(feature_size=1, d_model=16, num_layers=2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    
    # 3. Quick Train loop
    model.train()
    epochs = 20 # Increased epochs slightly
    
    for epoch in range(epochs): 
        optimizer.zero_grad()
        # Train to predict next step: Input[:-1] -> Target[1:]
        output = model(data_tensor[:-1])
        loss = criterion(output, data_tensor[1:])
        loss.backward()
        optimizer.step()
        
    # 4. Predict
    model.eval()
    predictions = []
    current_input = data_tensor
    
    with torch.no_grad():
        for _ in range(days_forecast):
            # Model takes full history to predict next step
            out = model(current_input)
            
            # Get the last prediction (next step)
            next_val = out[-1].item()
            
            # Denormalize
            pred_price = next_val * max_val
            predictions.append(pred_price)
            
            # Append prediction to input for autoregressive generation
            next_tensor = torch.FloatTensor([[[next_val]]])
            current_input = torch.cat((current_input, next_tensor), 0)
            
    # Return consistently rounded values (2 decimal places like dashboard)
    return [round(float(p), 2) for p in predictions]