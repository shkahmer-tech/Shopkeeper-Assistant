"""
Smart Shopkeeper Assistant — FastAPI entrypoint.

Run with:
    uvicorn app.main:app --reload
or:
    python app/main.py

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI,
where every route below can be tested directly in the browser.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import ai_review, charts, categories,delivery, demand, drivers, health, inventory, orders, report
from app.services.model_store import model_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: restore any models saved by a previous run so you don't
    # need to retrain after restarting the server.
    model_store.load_all()
    yield
    # (nothing needed on shutdown)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API for the Smart Shopkeeper Assistant: demand forecasting, "
        "inventory management, delivery time prediction, and AI-generated "
        "business reviews."
    ),
    lifespan=lifespan,
)

# Allow a local frontend (React/Vite/etc.) to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register every route group
app.include_router(health.router)
app.include_router(demand.router)
app.include_router(inventory.router)
app.include_router(delivery.router)
app.include_router(charts.router)
app.include_router(ai_review.router)
app.include_router(report.router)
app.include_router(orders.router)
app.include_router(drivers.router)
app.include_router(categories.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# Lets you run `python app/main.py` directly instead of the uvicorn CLI.
# The actual port lives in app/core/config.py (PORT setting) or a PORT
# value in your .env — change it there, not here.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )