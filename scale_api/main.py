import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from redis import asyncio as aioredis
from sqlalchemy import (Boolean, Column, DateTime, Integer, String, select,
                        update)
from sqlalchemy.ext.asyncio import (AsyncConnection, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import declarative_base, make_transient

logging.basicConfig(level=logging.INFO)

# โหลดค่าจาก .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'config.env'))

# Async PostgreSQL connection
SQLALCHEMY_DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL', 'sqlite:///./shortener.db')
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# Async Redis connection
redis = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

# Global listener instance
_notify_conn = None
_postgres_listener = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifespan."""

    # Get the Postgres listener and start listening
    postgres_listener = await get_postgres_listener()
    
    # Start processing notifications for each queue
    processing_tasks = []
    for queue in postgres_listener.listeners:
        task = asyncio.create_task(process_notification(queue))
        processing_tasks.append(task)

    yield  # Run the application

    # Stop the listener on application shutdown
    if _postgres_listener and _postgres_listener.listen_task:
        _postgres_listener.listen_task.cancel()
        try:
            await _postgres_listener.listen_task
        except asyncio.CancelledError:
            logging.info("Listener task was cancelled.")

    # Cancel all processing tasks
    for task in processing_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logging.info("Processing task was cancelled.")



# SQLAlchemy model
class URL(Base):
    """
    SQLAlchemy model for storing URL information.

    Attributes:
        id (int): The primary key for the URL record.
        key (str): The unique key representing the shortened URL.
        secret_key (str): A secret key associated with the URL.
        target_url (str): The target URL that the shortened URL points to.
        is_active (bool): Indicates if the URL is active.
        clicks (int): The number of times the URL has been accessed.
        created_at (datetime): Timestamp when the URL was created.
        updated_at (datetime): Timestamp when the URL was last updated.
        api_key (str): The API key associated with the URL.
        is_checked (bool): Indicates if the URL has been checked.
        status (str): The status of the URL.
        title (str): The title of the target webpage.
        favicon_url (str): The URL of the favicon for the target webpage.
    """
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    secret_key = Column(String, unique=True, index=True)
    target_url = Column(String, index=True)
    is_active = Column(Boolean)
    clicks = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    api_key = Column(String, index=True)
    is_checked = Column(Boolean, default=False)
    status = Column(String)
    title = Column(String(255))
    favicon_url = Column(String(255))

class PostgresListener:
    """
    https://github.com/TCatshoek/fastapi-postgres-sse
    https://tom.catshoek.dev/posts/postgres-sse/
    """
    def __init__(self, conn: AsyncConnection):
        self.conn = conn
        self.listen_task = None
        self.listeners = []

    async def start_listen_task(self):
        async def listen_task(conn: AsyncConnection) -> None:
            async for notify in conn.connection.notifies():
                # This is where notifications would normally be handled, 
                # but we use the add_listener method instead.
                pass

        self.listen_task = asyncio.create_task(listen_task(self.conn))

    def listen(self):
        queue = asyncio.Queue()
        self.listeners.append(queue)
        return queue

    def close(self, queue):
        self.listeners.remove(queue)


async def get_postgres_listener() -> PostgresListener:
    """
    Initializes and returns a PostgresListener instance.

    This function sets up a listener for PostgreSQL notifications on the 
    'url_change' channel. If the global connection (`_notify_conn`) is not 
    already established, it creates a new raw connection to the database and 
    uses `driver_connection` to add a listener for the 'url_change' channel. 
    If the global PostgresListener instance (`_postgres_listener`) is not 
    initialized, it creates and starts the listener.

    Returns:
        PostgresListener: The initialized PostgresListener instance.
    """
    global _notify_conn
    global _postgres_listener

    if _notify_conn is None:
        # Use raw_connection to get access to the native asyncpg connection
        _notify_conn = await engine.raw_connection()
        # Use the driver connection directly and add the url_change_handler
        await _notify_conn.driver_connection.add_listener('url_change', url_change_handler)

    if _postgres_listener is None:
        _postgres_listener = PostgresListener(_notify_conn)
        await _postgres_listener.start_listen_task()

        # Create a queue and add it to listeners for processing notifications
        queue = _postgres_listener.listen()
        asyncio.create_task(process_notification(queue))  # Start processing the queue

    return _postgres_listener


# Define the url_change_handler
def url_change_handler(conn, pid, channel, payload):
    """
    Callback function for handling PostgreSQL notifications.

    This function is triggered whenever a notification is received on the 
    'url_change' channel in PostgreSQL. It adds the payload to a queue for 
    asynchronous processing.

    Args:
        conn: The connection object that received the notification.
        pid (int): The process ID of the PostgreSQL backend that sent the notification.
        channel (str): The name of the channel on which the notification was sent.
        payload (str): The payload of the notification, typically in JSON format.
    """
    logging.info(f"Notification on channel {channel}: {payload}")
    
    # Add the payload to the queue for processing
    if _postgres_listener:
        for queue in _postgres_listener.listeners:
            asyncio.create_task(queue.put(payload))  # Add to the queue

async def process_notification(queue: asyncio.Queue):
    """
    Process notifications from the queue.

    Args:
        queue (asyncio.Queue): The queue from which to get the notifications.
    """
    while True:
        payload = await queue.get()
        if payload:
            try:
                # Process the payload
                payload_data = json.loads(payload)
                db_url = URL(**payload_data)

                # Sync the URL data to Redis
                await sync_to_redis(db_url)
                logging.info(f"Synced URL {db_url.key} to Redis.")
            except Exception as e:
                logging.error(f"Error processing notification payload: {e}")


# Async function to sync data from PostgreSQL to Redis
async def sync_to_redis(url: URL):
    """
    Syncs the given URL data to Redis.

    Args:
        url (URL): The URL object containing the data to sync.
    """
    url_data = {
        "id": url.id,
        "key": url.key,
        "secret_key": url.secret_key,
        "target_url": url.target_url,
        "is_active": url.is_active,
        "clicks": url.clicks,
        # Use the date strings directly from the payload
        "created_at": url.created_at if url.created_at else None,
        "updated_at": url.updated_at if url.updated_at else None,
        "api_key": url.api_key,
        "is_checked": url.is_checked,
        "status": url.status,
        "title": url.title,
        "favicon_url": url.favicon_url
    }
    await redis.set(f"url:{url.key}", json.dumps(url_data))

# FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Dependency to get DB session
async def get_db():
    """
    Dependency function to get an asynchronous database session.

    This function is used in route handlers to interact with the database.

    Yields:
        AsyncSession: An SQLAlchemy asynchronous session object.
    """
    async with AsyncSessionLocal() as session:
        yield session

# Background task to update PostgreSQL
async def update_db(key: str):
    """
    Background task to update the updated_at timestamp 
    and increment the click count for a given URL in PostgreSQL.

    Args:
        key (str): The key of the URL to update.
    """
    async with AsyncSessionLocal() as session:
        stmt = update(URL).where(URL.key == key).values(
            clicks=URL.clicks + 1,  # Increment the click count
            updated_at=datetime.now(timezone.utc)
        )
        await session.execute(stmt)
        await session.commit()

# Route to redirect to the target URL by key
@app.get("/{key}")
async def root_redirect(key: str, background_tasks: BackgroundTasks):
    """
    Redirect to the target URL by key using the get_url function to retrieve the URL data.

    Args:
        key (str): The key of the URL to redirect.
        background_tasks (BackgroundTasks): FastAPI background tasks to run asynchronously.

    Returns:
        RedirectResponse: Redirects to the target URL if found and active.

    Raises:
        HTTPException: If the URL is not found or inactive.
    """
    try:
        # Retrieve the URL data
        url_data = await get_url(key)
        
        # Update the clicks and updated_at timestamp in Redis
        url_data["clicks"] += 1
        url_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await redis.set(f"url:{key}", json.dumps(url_data))

        # Update PostgreSQL in the background
        background_tasks.add_task(update_db, key)

        # Perform the redirect to the target URL
        return RedirectResponse(url=url_data["target_url"])
    except HTTPException as e:
        # If the URL is not found, return the exception
        raise e


# Route to get URL by key
@app.get("/url/{key}")
async def get_url(key: str):
    """
    Retrieve URL data by key.

    This function checks Redis for the URL data. If found, it updates the click 
    count and updated_at timestamp in Redis and PostgreSQL asynchronously.
    If not found in Redis, it retrieves the data from PostgreSQL and syncs it to Redis.

    Args:
        key (str): The key of the URL to retrieve.
        background_tasks (BackgroundTasks): FastAPI background tasks to run asynchronously.

    Returns:
        dict: A dictionary containing the URL data.

    Raises:
        HTTPException: If the URL is not found.
    """
    # Try to get data from Redis
    url_data = await redis.get(f"url:{key}")
    if url_data:
        url_dict = json.loads(url_data)
        return url_dict
    else:
        # If not in Redis, get from PostgreSQL and sync to Redis
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(URL).filter(URL.key == key, URL.is_active == True))
            db_url = result.scalars().first()
            if db_url:
                # Sync to Redis
                await sync_to_redis(db_url)
                return {
                    "id": db_url.id,
                    "key": db_url.key,
                    "target_url": db_url.target_url,
                    "clicks": db_url.clicks,
                    "updated_at": db_url.updated_at.isoformat()
                }
    raise HTTPException(status_code=404, detail="URL not found")

# Route to create new URL
@app.post("/url")
async def create_url(url: dict, background_tasks: BackgroundTasks):
    """
    Create a new URL record in PostgreSQL and sync it to Redis if it's active.

    Args:
        url (dict): A dictionary containing the URL data to create.
        background_tasks (BackgroundTasks): FastAPI background tasks to run asynchronously.

    Returns:
        dict: A dictionary with a success message and the key of the created URL.
    """
    current_time = datetime.now(timezone.utc)
    url["created_at"] = current_time
    url["updated_at"] = current_time
    
    async with AsyncSessionLocal() as session:
        db_url = URL(**url)
        session.add(db_url)
        await session.commit()
        await session.refresh(db_url)
    
    # Sync to Redis in the background if the URL is active
    if db_url.is_active:
        background_tasks.add_task(sync_to_redis, db_url)
    
    return {"message": "URL created successfully", "key": db_url.key}


# Function to create tables
async def create_tables():
    """
    Create database tables based on the SQLAlchemy models.

    This function is used to create tables in the PostgreSQL database before
    running the FastAPI application.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Startup sync function
async def startup_sync():
    """
    Syncs all active URL data from PostgreSQL to Redis during application startup.
    """
    # Delete only keys that start with "url:"
    keys = await redis.keys("url:*")
    if keys:
        await redis.delete(*keys)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(URL).filter(URL.is_active == True))
        urls = result.scalars().all()
        for url in urls:
            await sync_to_redis(url)

async def main():
    """ main """
    config = uvicorn.Config(app, host="127.0.0.1", port=9000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
