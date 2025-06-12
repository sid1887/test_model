"""
FastAPI middleware for error handling, rate limiting, and security
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque
import structlog

logger = structlog.get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Deque[float]] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old entries
        while self.clients[client_ip] and self.clients[client_ip][0] <= now - self.period:
            self.clients[client_ip].popleft()
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.calls} requests per {self.period} seconds",
                    "retry_after": self.period
                }
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling middleware with structured logging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log successful requests with timing
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 3),
                client_ip=request.client.host
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(round(process_time, 3))
            return response
            
        except HTTPException as e:
            process_time = time.time() - start_time
            
            # Log HTTP exceptions
            logger.warning(
                "HTTP exception",
                method=request.method,
                url=str(request.url),
                status_code=e.status_code,
                detail=e.detail,
                process_time=round(process_time, 3),
                client_ip=request.client.host
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "status_code": e.status_code,
                    "timestamp": time.time(),
                    "path": str(request.url.path)
                }
            )
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log unexpected errors
            logger.error(
                "Unexpected error",
                method=request.method,
                url=str(request.url),
                error=str(e),
                error_type=type(e).__name__,
                process_time=round(process_time, 3),
                client_ip=request.client.host,
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "timestamp": time.time(),
                    "path": str(request.url.path),
                    "request_id": id(request)  # Simple request ID
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        })
        
        return response


class AIModelErrorMiddleware(BaseHTTPMiddleware):
    """Enhanced error handling middleware specifically for AI model failures"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Handle AI model specific errors
            if self._is_ai_model_error(exc):
                logger.error("AI model error", 
                           error=str(exc), 
                           error_type=type(exc).__name__,
                           endpoint=request.url.path)
                
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "AI Service Temporarily Unavailable",
                        "detail": "The AI analysis service is currently experiencing issues. Please try again in a few moments.",
                        "error_code": "AI_MODEL_ERROR",
                        "timestamp": time.time(),
                        "retry_after": 30
                    }
                )
            
            # Handle memory/resource errors
            elif self._is_resource_error(exc):
                logger.error("Resource error", 
                           error=str(exc), 
                           error_type=type(exc).__name__,
                           endpoint=request.url.path)
                
                return JSONResponse(
                    status_code=507,
                    content={
                        "error": "Insufficient Storage/Memory",
                        "detail": "The server is temporarily out of resources. Please try with a smaller image or try again later.",
                        "error_code": "RESOURCE_ERROR",
                        "timestamp": time.time(),
                        "retry_after": 60
                    }
                )
            
            # Handle CUDA/GPU errors
            elif self._is_gpu_error(exc):
                logger.error("GPU error", 
                           error=str(exc), 
                           error_type=type(exc).__name__,
                           endpoint=request.url.path)
                
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "GPU Processing Error",
                        "detail": "GPU processing is temporarily unavailable. Falling back to CPU processing may take longer.",
                        "error_code": "GPU_ERROR",
                        "timestamp": time.time(),
                        "retry_after": 15
                    }
                )
            
            # Handle image processing errors
            elif self._is_image_error(exc):
                logger.warning("Image processing error", 
                             error=str(exc), 
                             error_type=type(exc).__name__,
                             endpoint=request.url.path)
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Image Processing Failed",
                        "detail": "The uploaded image could not be processed. Please ensure it's a valid image file (JPG, PNG, WebP).",
                        "error_code": "IMAGE_ERROR",
                        "timestamp": time.time()
                    }
                )
            
            # Handle timeout errors
            elif self._is_timeout_error(exc):
                logger.warning("Processing timeout", 
                             error=str(exc), 
                             error_type=type(exc).__name__,
                             endpoint=request.url.path)
                
                return JSONResponse(
                    status_code=504,
                    content={
                        "error": "Processing Timeout",
                        "detail": "The analysis took too long to complete. Please try with a smaller image or simpler analysis.",
                        "error_code": "TIMEOUT_ERROR",
                        "timestamp": time.time(),
                        "retry_after": 30
                    }
                )
            
            # Generic server error
            else:
                logger.error("Unexpected error", 
                           error=str(exc), 
                           error_type=type(exc).__name__,
                           endpoint=request.url.path)
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal Server Error",
                        "detail": "An unexpected error occurred while processing your request.",
                        "error_code": "INTERNAL_ERROR",
                        "timestamp": time.time()
                    }
                )
    
    def _is_ai_model_error(self, exc: Exception) -> bool:
        """Check if error is related to AI model loading/inference"""
        error_indicators = [
            "yolo", "clip", "model", "torch", "cuda", "inference",
            "RuntimeError", "ModelManager", "ProductAnalyzer"
        ]
        error_str = str(exc).lower()
        error_type = type(exc).__name__.lower()
        
        return any(indicator in error_str or indicator in error_type 
                  for indicator in error_indicators)
    
    def _is_resource_error(self, exc: Exception) -> bool:
        """Check if error is related to insufficient resources"""
        resource_indicators = [
            "memory", "storage", "disk", "space", "out of memory",
            "memoryerror", "oserror"
        ]
        error_str = str(exc).lower()
        error_type = type(exc).__name__.lower()
        
        return any(indicator in error_str or indicator in error_type 
                  for indicator in resource_indicators)
    
    def _is_gpu_error(self, exc: Exception) -> bool:
        """Check if error is GPU/CUDA related"""
        gpu_indicators = [
            "cuda", "gpu", "device", "cudnn", "cublas", "nvidia"
        ]
        error_str = str(exc).lower()
        
        return any(indicator in error_str for indicator in gpu_indicators)
    
    def _is_image_error(self, exc: Exception) -> bool:
        """Check if error is image processing related"""
        image_indicators = [
            "image", "cv2", "opencv", "pil", "jpeg", "png", "format",
            "decode", "corrupted", "invalid image"
        ]
        error_str = str(exc).lower()
        error_type = type(exc).__name__.lower()
        
        return any(indicator in error_str or indicator in error_type 
                  for indicator in image_indicators)
    
    def _is_timeout_error(self, exc: Exception) -> bool:
        """Check if error is timeout related"""
        timeout_indicators = [
            "timeout", "time", "asyncio.timeouterror", "timeoutexception"
        ]
        error_str = str(exc).lower()
        error_type = type(exc).__name__.lower()
        
        return any(indicator in error_str or indicator in error_type 
                  for indicator in timeout_indicators)


def setup_middleware(app):
    """Setup all middleware in correct order"""
    
    # Add security headers (first)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add AI-specific error handling
    app.add_middleware(AIModelErrorMiddleware)
    
    # Add general error handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add rate limiting (last middleware)
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    
    logger.info("All middleware configured successfully")
