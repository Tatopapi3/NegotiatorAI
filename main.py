from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.ingest import router as ingest_router
from api.negotiate import router as negotiate_router
from api.observe import router as observe_router

app = FastAPI(
    title="NegotiateIQ",
    description="AI-powered salary negotiation coach for tech candidates. "
                "Uses RAG over real job descriptions and candidate profiles to give "
                "Claude the market context it needs to coach you with real numbers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(negotiate_router)
app.include_router(observe_router)


@app.get("/", tags=["health"])
def root():
    return {
        "service": "NegotiateIQ",
        "status": "running",
        "docs": "/docs",
    }
