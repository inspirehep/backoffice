import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from backoffice.users.models import User
from backoffice.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


class Migrator:
    def __init__(self, connection=connection):
        self.executor = MigrationExecutor(connection)

    def migrate(self, app_label: str, migration: str):
        target = [(app_label, migration)]
        self.executor.loader.build_graph()
        self.executor.migrate(target)
        self.apps = self.executor.loader.project_state(target).apps


@pytest.fixture
def migrator():
    return Migrator
