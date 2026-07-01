from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src import exceptions
from src.admin.router import router as admin_router
from src.cart.router import router as cart_router
from src.config import SHOW_DOCS_IN, settings
from src.customers.router import router as customers_router
from src.database import engine
from src.images.router import router as images_router
from src.logging_config import configure_logging, get_logger
from src.orders.router import router as orders_router
from src.payments.router import router as payments_router
from src.products.router import router as products_router
from src.seed import run_migrations, seed_initial_data
from src.shipping.router import router as shipping_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = get_logger("app.lifespan")
    logger.info("starting_up", environment=settings.ENVIRONMENT)
    try:
        await run_migrations()
        logger.info("migrations_complete")
    except Exception:
        logger.exception("migrations_failed")
        raise
    try:
        await seed_initial_data()
        logger.info("seeding_complete")
    except Exception:
        logger.exception("seeding_failed")
        raise
    yield
    logger.info("shutting_down")
    await engine.dispose()


app_kwargs: dict = {
    "title": "Ecommerce API",
    "lifespan": lifespan,
    "openapi_url": f"{settings.API_V1_PREFIX}/openapi.json",
}
if settings.ENVIRONMENT not in SHOW_DOCS_IN:
    app_kwargs["openapi_url"] = None

app = FastAPI(**app_kwargs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = get_logger("app.http")
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    if request.url.path != "/health":
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
    return response


# ── Routers ───────────────────────────────────────────────


app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(cart_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(images_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(shipping_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(exceptions.AppException)
async def app_exception_handler(request: Request, exc: exceptions.AppException):
    logger = get_logger("app.errors")
    logger.warning(
        "app_exception",
        path=request.url.path,
        status=exc.status_code,
        code=exc.code,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
