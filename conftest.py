import datetime
import os
import uuid
from typing import Any, AsyncGenerator, Callable, Generator, cast

import pytest
import taskiq_fastapi
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from pytest import Parser
from pytest_asyncio import is_async_test
from pytest_mock import MockerFixture
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession
from sqlalchemy.orm import Session, SessionTransaction

from apps.answers.deps.preprocess_arbitrary import get_answer_session
from apps.shared.test.client import TestClient
from broker import broker
from config import settings
from infrastructure.app import create_app
from infrastructure.database.core import build_engine
from infrastructure.database.deps import get_session

pytest_plugins = [
    "apps.activities.tests.fixtures.configs",
    "apps.activities.tests.fixtures.response_values",
    "apps.activities.tests.fixtures.items",
    "apps.activities.tests.fixtures.conditional_logic",
    "apps.activities.tests.fixtures.scores_reports",
    "apps.activities.tests.fixtures.activities",
    "apps.users.tests.fixtures.users",
    "apps.applets.tests.fixtures.applets",
]


# TODO: Instead of custom faketime for tests add function wrapper `now`
# to use it instead of builtin datetime.datetime.utcnow
class FakeTime(datetime.datetime):
    current_utc = datetime.datetime(2024, 1, 1, 0, 0, 0)

    @classmethod
    def utcnow(cls):
        return cls.current_utc


alembic_configs = [Config("alembic.ini"), Config("alembic_arbitrary.ini")]


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--keepdb",
        action="store_true",
        default=False,
        help="If keepdb is true, then migrations wont be downgraded after tests",  # noqa: E501
    )


def before():
    os.environ["PYTEST_APP_TESTING"] = "1"
    for alembic_cfg in alembic_configs:
        command.upgrade(alembic_cfg, "head")


def after():
    for alembic_cfg in alembic_configs[::-1]:
        command.downgrade(alembic_cfg, "base")
    os.environ.pop("PYTEST_APP_TESTING", None)


def pytest_sessionstart(session) -> None:
    before()


def pytest_sessionfinish(session) -> None:
    keepdb = session.config.getvalue("keepdb")
    if not keepdb:
        after()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return create_app()


@pytest.fixture(scope="session")
def arbitrary_db_url() -> str:
    host = settings.database.host
    return f"postgresql+asyncpg://postgres:postgres@{host}:5432/test_arbitrary"


@pytest.fixture()
async def engine() -> AsyncGenerator[AsyncEngine, Any]:
    engine = build_engine(settings.database.url)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def arbitrary_engine(
    arbitrary_db_url: str,
) -> AsyncGenerator[AsyncEngine, Any]:
    engine = build_engine(arbitrary_db_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator:
    async with engine.begin() as conn:
        conn = cast(AsyncConnection, conn)
        await conn.begin_nested()
        async with AsyncSession(bind=conn) as async_session:

            @event.listens_for(async_session.sync_session, "after_transaction_end")
            def end_savepoint(session: Session, transaction: SessionTransaction) -> None:
                nonlocal conn
                conn = cast(AsyncConnection, conn)
                if conn.closed:
                    return
                if not conn.in_nested_transaction():
                    if conn.sync_connection:
                        conn.sync_connection.begin_nested()

            yield async_session
        await conn.rollback()


@pytest.fixture
async def arbitrary_session(arbitrary_engine: AsyncEngine) -> AsyncGenerator:
    async with arbitrary_engine.begin() as conn:
        conn = cast(AsyncConnection, conn)
        await conn.begin_nested()
        async with AsyncSession(bind=conn) as async_session:

            @event.listens_for(async_session.sync_session, "after_transaction_end")
            def end_savepoint(session: Session, transaction: SessionTransaction) -> None:
                if conn.closed:
                    return
                if not conn.in_nested_transaction():
                    if conn.sync_connection:
                        conn.sync_connection.begin_nested()

            yield async_session
        await conn.rollback()


@pytest.fixture
def client(session: AsyncSession, app: FastAPI) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    taskiq_fastapi.populate_dependency_context(broker, app)
    client = TestClient(app)
    return client


@pytest.fixture
def arbitrary_client(
    app: FastAPI, session: AsyncSession, arbitrary_session: AsyncSession
) -> Generator[TestClient, None, None]:
    """Use only for tests which interact with arbitrary servers, because
    arbitrary (answers) session has higher prioritet then general session.
    """
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_answer_session] = lambda: arbitrary_session
    taskiq_fastapi.populate_dependency_context(broker, app)
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_answer_session)


def pytest_collection_modifyitems(items) -> None:
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker)


@pytest.fixture
def remote_image() -> str:
    # TODO: add support for localimages for tests
    return "https://www.w3schools.com/css/img_5terre_wide.jpg"


@pytest.fixture
async def mock_kiq_report(mocker) -> AsyncGenerator[Any, Any]:
    mock = mocker.patch("apps.answers.service.create_report.kiq")
    yield mock


@pytest.fixture
async def mock_report_server_response(mocker) -> AsyncGenerator[Any, Any]:
    Recipients = list[str]
    FakeBody = dict[str, str | dict[str, str | Recipients]]

    def json_() -> FakeBody:
        return dict(
            pdf="cGRmIGJvZHk=",
            email=dict(
                body="Body",
                subject="Subject",
                attachment="Attachment name",
                emailRecipients=["tom@cmiml.net"],
            ),
        )

    mock = mocker.patch("aiohttp.ClientSession.post")
    mock.return_value.__aenter__.return_value.status = 200
    mock.return_value.__aenter__.return_value.json.side_effect = json_
    yield mock


@pytest.fixture
async def mock_reencrypt_kiq(mocker) -> AsyncGenerator[Any, Any]:
    mock = mocker.patch("apps.users.api.password.reencrypt_answers.kiq")
    yield mock


@pytest.fixture(scope="session")
def uuid_zero() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000000")


@pytest.fixture
def faketime(mocker: MockerFixture) -> type[FakeTime]:
    mock = mocker.patch("datetime.datetime", new=FakeTime)
    return mock


@pytest.fixture
def mock_get_session(
    session: AsyncSession,
    arbitrary_session: AsyncSession,
    mocker: MockerFixture,
    arbitrary_db_url: str,
) -> Callable[..., Callable[[], AsyncSession]]:
    # Add stub for first argument, because orig get_session takes instanace as first argument after mock
    def get_session(_, url: str = settings.database.url) -> Callable[[], AsyncSession]:
        def f() -> AsyncSession:
            if url == arbitrary_db_url:
                return arbitrary_session
            return session

        return f

    mock = mocker.patch(
        "infrastructure.database.core.SessionManager.get_session",
        new=get_session,
    )
    return mock
