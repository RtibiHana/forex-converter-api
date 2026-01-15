# app/main.py - Forex Converter API (Version DevOps Complète)
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from datetime import datetime
import time
import logging
import uuid
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ==================== CONFIGURATION ====================
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "service": "forex-api", "request_id": "%(request_id)s", "path": "%(pathname)s"}'
)
logger = logging.getLogger(__name__)

# ==================== METRICS PROMETHEUS ====================
REQUEST_COUNT = Counter(
    'forex_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'forex_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)
CONVERSION_COUNT = Counter(
    'forex_conversions_total',
    'Total currency conversions',
    ['from_currency', 'to_currency']
)

# ==================== APPLICATION ====================
app = FastAPI(
    title="Forex Converter API",
    description="A cloud-native currency conversion microservice with full DevOps implementation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==================== DONNÉES ====================
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 151.50,
    "CAD": 1.36,
    "AUD": 1.49,
    "CHF": 0.89,
    "CNY": 7.23,
    "INR": 83.33,
    "MAD": 10.07,
    "BTC": 0.000015
}

# ==================== MODÈLES ====================
class ConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    uptime: float

# ==================== MIDDLEWARE OBSERVABILITY ====================
@app.middleware("http")
async def add_observability(request, call_next):
    start_time = time.time()
    
    # Générer un ID unique pour la requête
    request_id = str(uuid.uuid4())
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status="pending").inc()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(process_time)
    
    # Update request count with actual status
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    
    # Add headers for tracing avec UUID unique
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-ID"] = request_id  # Pour compatibilité avec les systèmes de tracing
    
    # Structured logging avec request_id
    logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.3f}s - Request-ID: {request_id}")
    
    return response

# ==================== ENDPOINTS ====================
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the Forex Converter API",
        "version": "1.0.0",
        "endpoints": {
            "/docs": "Interactive documentation",
            "/health": "Health check",
            "/metrics": "Prometheus metrics",
            "/currencies": "List available currencies",
            "/convert": "Currency conversion (POST)"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring and readiness probes"""
    return {
        "status": "healthy",
        "service": "forex-converter-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - app_start_time
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for observability"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/currencies")
async def list_currencies():
    """List all available currencies for conversion"""
    return {
        "available_currencies": list(EXCHANGE_RATES.keys()),
        "base_currency": "USD",
        "count": len(EXCHANGE_RATES),
        "timestamp": datetime.utcnow().isoformat()
    }

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
        logger.error(f"Unsupported source currency: {from_curr}")
        raise HTTPException(status_code=400, detail=f"Unsupported source currency: {from_curr}")
    if to_curr not in EXCHANGE_RATES:
        logger.error(f"Unsupported target currency: {to_curr}")
        raise HTTPException(status_code=400, detail=f"Unsupported target currency: {to_curr}")
    if conversion.amount <= 0:
        logger.error(f"Invalid amount: {conversion.amount}")
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # Perform conversion (via USD as base)
    try:
        amount_in_usd = conversion.amount / EXCHANGE_RATES[from_curr]
        converted_amount = amount_in_usd * EXCHANGE_RATES[to_curr]
        rate = EXCHANGE_RATES[to_curr] / EXCHANGE_RATES[from_curr]

        # Metrics and structured logging
        CONVERSION_COUNT.labels(from_currency=from_curr, to_currency=to_curr).inc()
        logger.info(f"Conversion: {conversion.amount} {from_curr} -> {converted_amount:.2f} {to_curr} (rate: {rate:.4f})")

        return {
            "original_amount": conversion.amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "converted_amount": round(converted_amount, 4),
            "exchange_rate": round(rate, 6),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal conversion error")

# ==================== GLOBAL VARIABLES ====================
app_start_time = time.time()

# ==================== EXECUTION ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)