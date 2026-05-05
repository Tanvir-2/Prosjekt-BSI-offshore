from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_URL
from database import engine, Base
from models.user import User
from models.audit_log import AuditLog
from services.watcher import BSIWatcher
from routers.auth import router as auth_router
from routers.search import router as search_router
from routers.documents import router as docs_router
from routers.admin import router as admin_router

# Global watcher instance
watcher = BSIWatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables, setup Meilisearch, start file watcher."""
    
    Base.metadata.create_all(bind=engine)

    
    from services.meili_service import setup_index, get_document_count
    setup_index()

    
    if get_document_count() == 0:
        from services.meili_service import bulk_index
        from config import DATA_FOLDER
        bulk_index(DATA_FOLDER)

    
    watcher.start()

    yield

    
    watcher.stop()


app = FastAPI(
    title="BSI Document Search Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(search_router)
app.include_router(docs_router)
app.include_router(admin_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "BSI Search Engine",
        "watcher": watcher.status(),
    }
