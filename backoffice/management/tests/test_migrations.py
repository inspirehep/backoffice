import pytest


@pytest.mark.django_db
def test_populate_emails(migrator):
    migrator = migrator()
    migrator.migrate("management", "0001_initial")
    Group = migrator.apps.get_model("auth", "Group")
    all_groups = Group.objects.all()
    assert len(all_groups) == 2
