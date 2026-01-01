# app/main.py - Forex Converter API (Core Logic)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Forex Converter API",
    description="A cloud-native API for currency conversion with DevOps practices.",
    version="1.0.0"
)

# In-memory data store for exchange rates (simplified)
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 151.50,
    "CAD": 1.36,
    "MAD": 10.07,  # Moroccan Dirham
    "BTC": 0.000015  # Bitcoin for fun
}

# Pydantic model for request validation
class ConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

# Health check endpoint (Critical for DevOps monitoring)
@app.get("/health")
async def health():
    """Health check endpoint for monitoring and readiness probes."""
    return {
        "status": "healthy",
        "service": "forex-converter-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Forex Converter API",
        "endpoints": {
            "/health": "GET - Service health check",
            "/currencies": "GET - List all supported currencies",
            "/convert": "POST - Convert between currencies"
        },
        "documentation": "/docs"
    }

# List available currencies
@app.get("/currencies")
async def list_currencies():
    """List all available currencies for conversion."""
    return {
        "available_currencies": list(EXCHANGE_RATES.keys()),
        "base_currency": "USD",
        "count": len(EXCHANGE_RATES)
    }

# Core conversion endpoint
@app.post("/convert")
async def convert(conversion: ConversionRequest):
    """
    Convert an amount from one currency to another.
    Example: {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}
    """
    from_curr = conversion.from_currency.upper()
    to_curr = conversion.to_currency.upper()

    # Input validation
    if from_curr not in EXCHANGE_RATES:
        raise HTTPException(status_code=400, detail=f"Unsupported source currency: {from_curr}")
    if to_curr not in EXCHANGE_RATES:
        raise HTTPException(status_code=400, detail=f"Unsupported target currency: {to_curr}")
    if conversion.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # Perform conversion (via USD as base)
    try:
        amount_in_usd = conversion.amount / EXCHANGE_RATES[from_curr]
        converted_amount = amount_in_usd * EXCHANGE_RATES[to_curr]
        rate = EXCHANGE_RATES[to_curr] / EXCHANGE_RATES[from_curr]

        # Log the conversion (structured logging)
        logger.info(f"Conversion: {conversion.amount} {from_curr} -> {converted_amount:.2f} {to_curr}")

        return {
            "original_amount": conversion.amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "converted_amount": round(converted_amount, 4),
            "exchange_rate": round(rate, 6),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(status_code=500, detail="Internal conversion error")

# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)