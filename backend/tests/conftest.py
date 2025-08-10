"""
Shared test configuration and fixtures for the Deep Insight backend tests.
"""

import pytest
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from py_pglite.config import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

from app.main import app
from app.db import get_session
from app.models.models import Business, Employee

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def pglite_manager() -> Generator[SQLAlchemyPGliteManager, None, None]:
    """Create a PGlite database manager for the test session."""
    # Create unique configuration to prevent socket conflicts
    config = PGliteConfig()

    # Create a unique socket directory for this test session
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


@pytest.fixture(name="session")
def session_fixture(
    pglite_manager: SQLAlchemyPGliteManager,
) -> Generator[Session, None, None]:
    """Create a test database session using PGlite with proper cleanup."""
    engine = pglite_manager.get_engine()

    # Create tables
    SQLModel.metadata.create_all(engine)

    # Create session
    session = Session(engine)

    try:
        yield session
    finally:
        # Clean up after each test
        try:
            # Clean up data in reverse dependency order
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
            session.rollback()
        finally:
            session.close()


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


@pytest.fixture(scope="session")
def test_server(pglite_manager: SQLAlchemyPGliteManager):
    """Start a test server with PGlite database."""
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

    # Override the database session to use our test database
    engine = pglite_manager.get_engine()
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

    # Create server instance
    config = uvicorn.Config(
        app=app, host="127.0.0.1", port=port, log_level="error", access_log=False
    )
    server = uvicorn.Server(config)

    # Run server in thread
    def run_server():
        asyncio.run(server.serve())

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
