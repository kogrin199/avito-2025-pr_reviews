from fastapi import FastAPI

from app.api.pr import router as pr_router
from app.api.review import router as review_router
from app.api.team import router as team_router
from app.api.user import router as user_router

app = FastAPI(title="PR Reviewer Assignment Service", version="1.0.0")

app.include_router(team_router)
app.include_router(user_router)
app.include_router(pr_router)
app.include_router(review_router)

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
