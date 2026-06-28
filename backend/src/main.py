from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src import exceptions
from src.admin.router import router as admin_router
from src.auth.router import router as auth_router
from src.cart.router import router as cart_router
from src.config import SHOW_DOCS_IN, settings
from src.customers.router import router as customers_router
from src.database import engine
from src.orders.router import router as orders_router
from src.payments.router import router as payments_router
from src.products.router import router as products_router
from src.seed import run_migrations, seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    await seed_initial_data()
    yield
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

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(cart_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(exceptions.AppException)
async def app_exception_handler(_, exc: exceptions.AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
