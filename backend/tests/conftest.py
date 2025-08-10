"""
Shared test configuration and fixtures for the Deep Insight backend tests.
"""

import pytest
import logging
import tempfile
import uuid
import time
from pathlib import Path
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, text
from py_pglite.config import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

from app.main import app
from app.db import get_session
from app.models.models import Business, Employee

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def pglite_manager() -> Generator[SQLAlchemyPGliteManager, None, None]:
    """Create a PGlite database manager for the test module - much faster than per-function."""
    # Create unique configuration to prevent socket conflicts
    config = PGliteConfig()

    # Create a unique socket directory for this test module
    # PGlite expects socket_path to be the full path including .s.PGSQL.5432
    socket_dir = Path(tempfile.gettempdir()) / f"py-pglite-test-{uuid.uuid4().hex[:8]}"
    socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
    config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    manager = SQLAlchemyPGliteManager(config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="module")
def pglite_engine(pglite_manager: SQLAlchemyPGliteManager):
    """Get the SQLAlchemy engine from the PGlite manager."""
    return pglite_manager.get_engine()


def _clean_database_data(engine):
    """Clean all data from database tables efficiently."""
    retry_count = 3
    for attempt in range(retry_count):
        try:
            with engine.connect() as conn:
                # Get all table names from our models
                result = conn.execute(
                    text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
                )

                table_names = [row[0] for row in result]
                logger.debug(f"Found tables to clean: {table_names}")

                if table_names:
                    # Disable foreign key checks for faster cleanup
                    conn.execute(text("SET session_replication_role = replica;"))

                    # Truncate all tables
                    for table_name in table_names:
                        conn.execute(
                            text(
                                f'TRUNCATE TABLE "{table_name}" '
                                "RESTART IDENTITY CASCADE;"
                            )
                        )

                    # Re-enable foreign key checks
                    conn.execute(text("SET session_replication_role = DEFAULT;"))

                    # Commit the cleanup
                    conn.commit()
                    logger.debug("Database cleanup completed successfully")
                else:
                    logger.debug("No tables found to clean")
                break  # Success, exit retry loop

        except Exception as e:
            logger.debug(f"Database cleanup attempt {attempt + 1} failed: {e}")
            if attempt == retry_count - 1:
                logger.warning(
                    "Database cleanup failed after all retries, continuing anyway"
                )
            else:
                time.sleep(0.1)  # Brief pause before retry


@pytest.fixture(name="session")
def session_fixture(
    pglite_engine,
) -> Generator[Session, None, None]:
    """Create a test database session with efficient cleanup between tests."""
    # Create tables once per module
    SQLModel.metadata.create_all(pglite_engine)
    
    # Clean up data before test starts
    _clean_database_data(pglite_engine)

    # Create session
    session = Session(pglite_engine)

    try:
        yield session
    finally:
        # Close the session safely
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
        
        # Clean up data after test completes for next test
        _clean_database_data(pglite_engine)


@pytest.fixture(name="test_business")
def test_business_fixture(session: Session):
    """Create a test business for use in employee tests."""
    business = Business(name="Test Company")
    session.add(business)
    session.commit()
    session.refresh(business)
    return business


@pytest.fixture(name="sample_employee_data")
def sample_employee_data_fixture(test_business: Business):
    """Provide sample employee data for testing."""
    return {
        "email": "john.doe@testcompany.com",
        "bio": "Software Engineer with 5 years experience",
        "business_id": str(test_business.id),
    }


@pytest.fixture(name="updated_employee_data")
def updated_employee_data_fixture(test_business: Business):
    """Provide updated employee data for testing."""
    return {
        "email": "john.smith@testcompany.com",
        "bio": "Senior Software Engineer with 8 years experience",
        "business_id": str(test_business.id),
    }


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with dependency override for direct testing."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def test_server(pglite_engine):
    """Start a test server with PGlite database for the test module."""
    import uvicorn
    import threading
    import socket
    import time
    import asyncio
    from contextlib import closing

    # Find an available port
    def find_free_port():
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    port = find_free_port()

    # Use the passed engine instead of creating a new one
    engine = pglite_engine
    from sqlmodel import Session, SQLModel

    # Create tables in the test database
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        return Session(engine)

    # Override the database engine and functions before importing the app
    import app.db as db_module

    db_module.engine = engine

    # Override create_db_and_tables to use our test engine
    def create_test_db_and_tables():
        SQLModel.metadata.create_all(engine)

    db_module.create_db_and_tables = create_test_db_and_tables

    from app.main import app
    from app.db import get_session

    app.dependency_overrides[get_session] = get_test_session

    # Create server instance with verbose logging
    config = uvicorn.Config(
        app=app, host="127.0.0.1", port=port, log_level="debug", access_log=True
    )
    server = uvicorn.Server(config)

    # Run server in thread with real-time logging
    def run_server():
        try:
            # Configure logging to show server output in real-time
            import logging
            import sys
            
            # Clear any existing handlers to avoid duplicates
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Set up a custom formatter for server logs
            formatter = logging.Formatter('[SERVER] %(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            
            # Configure root logger to capture everything
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(handler)
            
            # Configure specific loggers
            uvicorn_logger = logging.getLogger("uvicorn")
            uvicorn_logger.setLevel(logging.DEBUG)
            
            # Configure app loggers (this will capture our LLM logs)
            app_logger = logging.getLogger("app")
            app_logger.setLevel(logging.DEBUG)
            
            # Configure our specific service logger
            service_logger = logging.getLogger("app.services.next_question_service")
            service_logger.setLevel(logging.DEBUG)
            
            print(f"[SERVER] Starting test server on port {port}...", flush=True)
            print(f"[SERVER] Logger configured - will show LLM integration logs", flush=True)
            asyncio.run(server.serve())
        except Exception as e:
            print(f"[SERVER] Server error: {e}", file=sys.stderr, flush=True)
            raise

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    import requests

    max_retries = 20
    for i in range(max_retries):
        try:
            response = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
            if response.status_code == 200:
                break
        except Exception as e:
            time.sleep(0.5)
    else:
        raise RuntimeError(f"Test server failed to start on port {port}")

    yield f"http://127.0.0.1:{port}"

    # Cleanup
    app.dependency_overrides.clear()
    if hasattr(server, "should_exit"):
        server.should_exit = True


@pytest.fixture(name="api_client")
def api_client_fixture(test_server: str):
    """Create an API client instance for testing."""
    from deep_insight_client import ApiClient, Configuration

    config = Configuration(host=test_server)
    api_client = ApiClient(configuration=config)

    return api_client


@pytest.fixture(name="employees_api")
def employees_api_fixture(api_client):
    """Create an EmployeesApi instance for testing."""
    from deep_insight_client import EmployeesApi

    return EmployeesApi(api_client)


@pytest.fixture(name="businesses_api")
def businesses_api_fixture(api_client):
    """Create a BusinessesApi instance for testing."""
    from deep_insight_client import BusinessesApi

    return BusinessesApi(api_client)
