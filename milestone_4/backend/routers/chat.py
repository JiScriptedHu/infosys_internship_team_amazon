from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import yfinance as yf

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fast fetch of current price
        return stock.fast_info.last_price
    except:
        return None

@router.post("/")
async def chat_response(request: ChatRequest):
    user_msg = request.message.lower().strip()
    
    # 1. Price Inquiry Logic (Simple Regex-like check)
    # Detects patterns like "price of INFY" or "INFY price"
    words = user_msg.split()
    potential_ticker = None
    
    # Simple heuristic to find ticker (uppercase word or word with .NS)
    for word in request.message.split():
        clean_word = word.strip("?.!,")
        if clean_word.isupper() or ".NS" in clean_word:
            potential_ticker = clean_word
            break
            
    if "price" in user_msg and potential_ticker:
        price = get_stock_price(potential_ticker)
        if price:
            return {"response": f"The current market price of {potential_ticker} is {price:.2f}."}
        else:
            return {"response": f"I couldn't fetch data for {potential_ticker}. Please check the ticker symbol."}

    # 2. General Responses
    responses = {
        "hello": "Hello! I am your AI Financial Assistant. Ask me about stock prices or market trends.",
        "hi": "Hi there! How can I help you with your portfolio today?",
        "buy": "As an AI, I cannot provide financial advice. However, technical indicators suggest looking at RSI and MACD before making a decision.",
        "sell": "Selling decisions should be based on your risk tolerance and target price. Check the forecast tab for AI predictions.",
        "forecast": "You can view detailed AI predictions on the 'Forecast' page available in the sidebar.",
        "thanks": "You're welcome! Happy trading.",
        "default": [
            "I'm designed to analyze market data. You can ask me 'What is the price of INFY.NS?'",
            "Could you clarify? I can help with stock prices and basic technical concepts.",
            "I'm tracking the markets. Try asking about a specific stock ticker."
        ]
    }

    # Check for keywords
    for key in responses:
        if key in user_msg and key != "default":
            return {"response": responses[key]}

    # Default fallback
    return {"response": random.choice(responses["default"])}