from fastapi import FastAPI,Request
from routers import employee, request, project,auth,login
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
import logging.handlers
from starlette.middleware.base import BaseHTTPMiddleware


# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", mode='a'),  # Write logs to a file named 'app.log'
        logging.StreamHandler()  # Keep the console output
    ]
)
logger = logging.getLogger(__name__)


app = FastAPI()
logger.info("Starting API....")

#Create a log of the http requests and responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"{request.client.host}:{request.client.port} - \"{request.method} {request.url.path} HTTP/1.1\"")
        response = await call_next(request)
        logger.info(f"{request.client.host}:{request.client.port} - \"{request.method} {request.url.path} HTTP/1.1\" {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

templates = Jinja2Templates(directory="..\\frontend\\templates")
app.include_router(employee.router)
app.include_router(auth.router)
app.include_router(login.router)
app.include_router(request.router)
app.include_router(project.router)


#################################################################################################################################

# Functions to render html pages

@app.get('/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("menu.html",context)

@app.get('/emp_details/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("emp_details.html",context)


@app.get('/logout/',response_class=HTMLResponse)
def index(request: Request):
    context = {'request' : request}
    return templates.TemplateResponse("logout.html",context)