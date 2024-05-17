from fastapi import FastAPI
from routers import employee, request, project,auth

app = FastAPI()

app.include_router(employee.router)
app.include_router(auth.router)
app.include_router(request.router)
app.include_router(project.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
