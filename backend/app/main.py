from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import books, members, borrowings

app = FastAPI(
    title="Neighborhood Library Service",
    description="Manage books, members, and lending operations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(borrowings.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
