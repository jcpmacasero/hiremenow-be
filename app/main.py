# hiremenow-be/app/main.py
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.api.v1.router import api_router

settings = get_settings()

app = FastAPI(
    title="HireMeNow API",
    description="Recruitment Agency Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Parse CORS origins
origins = [origin.strip() for origin in settings.cors_origins.split(",")] if settings.cors_origins else []
# In development, ensure localhost origins are included
if settings.environment == "development":
    dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
    for dev_origin in dev_origins:
        if dev_origin not in origins:
            origins.append(dev_origin)

# Custom CORS middleware that handles both OPTIONS and regular requests
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin")
        
        # Handle OPTIONS preflight requests
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            # In development, allow any origin
            if settings.environment == "development":
                response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            elif origin and origin in origins:
                response.headers["Access-Control-Allow-Origin"] = origin
            elif origins:
                response.headers["Access-Control-Allow-Origin"] = origins[0]
            else:
                response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # Handle regular requests - add CORS headers to response
        response = await call_next(request)
        
        # Add CORS headers to response
        if settings.environment == "development":
            response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        elif origin and origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif origins:
            response.headers["Access-Control-Allow-Origin"] = origins[0]
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response

app.add_middleware(CustomCORSMiddleware)

# Exception handler for validation errors on OPTIONS requests
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin")
        response = Response(status_code=200)
        if origin and origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif origins:
            response.headers["Access-Control-Allow-Origin"] = origins[0]
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    # For non-OPTIONS requests, let FastAPI handle the error normally
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Add explicit OPTIONS handler for all API routes before including routers
@app.options("/api/{full_path:path}")
async def options_handler(full_path: str, request: Request):
    """Handle OPTIONS preflight requests for all API routes"""
    origin = request.headers.get("Origin")
    response = Response(status_code=200)
    if origin:
        if origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origins[0] if origins else "*"
    else:
        response.headers["Access-Control-Allow-Origin"] = origins[0] if origins else "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

app.include_router(api_router)

# Create uploads directory and mount static files
uploads_path = Path(settings.upload_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}
