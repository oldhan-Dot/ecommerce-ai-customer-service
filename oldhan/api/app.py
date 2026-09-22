from fastapi import FastAPI

from oldhan.api.routers import router

app = FastAPI()
app.include_router(router)
