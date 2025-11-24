from fastapi import FastAPI

app = FastAPI(title="PR Reviewer Assignment Service", version="1.0.0")

# Example healthcheck
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
