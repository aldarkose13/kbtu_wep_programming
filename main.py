from fastapi import FastAPI
from routers import registration

app = FastAPI()
app.include_router(registration.router)


@app.get("/")
def root():
    return {"App status": "Running"}
