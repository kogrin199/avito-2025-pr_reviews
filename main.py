from fastapi import FastAPI

app = FastAPI()

type Num = int | float


@app.post("/add")
async def add_(a: Num, b: Num):
    return {"result": a + b}


@app.post("/subtract")
async def sub_(a: Num, b: Num):
    return {"result": a - b}


@app.post("/multiply")
async def mul_(a: Num, b: Num):
    return {"result": a * b}
