from unittest.mock import MagicMock

import pytest

from intric.actors import SpaceActor
from intric.modules.module import Modules


# Mocking external dependencies
class MockUser:
    def __init__(self, user_id, permissions, modules):
        self.id = user_id
        self.permissions = permissions
        self.modules = modules


class MockSpace:
    def __init__(self, user_id, personal=False):
        self.user_id = user_id
        self.personal = personal

    def is_personal(self):
        return self.personal


class MockSpaceRole:
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class MockPermission:
    ASSISTANTS = "assistants"
    COLLECTIONS = "collections"
    WEBSITES = "websites"
    SERVICES = "services"


class MockSettings:
    using_intric_proprietary = True
    using_apps = True


SETTINGS = MockSettings()


@pytest.fixture
def owner_user():
    return MockUser(user_id=1, permissions=[], modules=[])


@pytest.fixture
def member_user():
    return MockUser(user_id=1, permissions=[], modules=[])


@pytest.fixture
def personal_space():
    return MockSpace(user_id=1, personal=True)


@pytest.fixture
def shared_space():
    return MockSpace(user_id=1, personal=False)


def test_owner_can_read_personal_space(owner_user: MockUser, personal_space: MockSpace):
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_read_space() is True


def test_owner_cannot_edit_personal_space(
    owner_user: MockUser, personal_space: MockSpace
):
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_edit_space() is False


def test_admin_can_edit_shared_space(member_user: MockUser, shared_space: MockSpace):
    actor = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert actor.can_edit_space() is True


def test_editor_cannot_edit_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    actor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert actor.can_edit_space() is False


def test_viewer_cannot_edit_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    actor = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert actor.can_edit_space() is False


def test_owner_can_create_websites_with_proprietary_feature_on(
    owner_user: MockUser, personal_space: MockSpace
):
    owner_user.permissions.append(MockPermission.WEBSITES)
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_create_websites() is True


def test_owner_cannot_create_websites_with_proprietary_feature_off(
    owner_user: MockUser, personal_space: MockSpace
):
    SETTINGS.using_intric_proprietary = False
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_create_websites() is False
    SETTINGS.using_intric_proprietary = True  # Reset for other tests


def test_owner_can_not_create_services_without_services_permission(
    owner_user: MockUser, personal_space: MockSpace
):
    owner_user.modules.append(Modules.INTRIC_APPLICATIONS)
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_create_services() is False

    owner_user.permissions.append(MockPermission.SERVICES)
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_create_services() is True


def test_no_one_can_publish_apps_in_personal_space(
    owner_user: MockUser, personal_space: MockSpace
):
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_publish_apps() is False


def test_only_admins_can_publish_apps_in_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_publish_apps() is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_publish_apps() is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_publish_apps() is True


def test_only_admins_can_edit_and_delete_published_apps(
    member_user: MockUser, shared_space: MockSpace
):
    app = MagicMock(published=True)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_edit_app(app=app) is False
    assert viewer.can_delete_app(app=app) is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_edit_app(app=app) is False
    assert editor.can_delete_app(app=app) is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_edit_app(app=app) is True
    assert admin.can_delete_app(app=app) is True


def test_no_one_can_publish_assistants_in_personal_space(
    owner_user: MockUser, personal_space: MockSpace
):
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_publish_assistants() is False


def test_only_admins_can_publish_assistants_in_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_publish_assistants() is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_publish_assistants() is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_publish_assistants() is True


def test_only_admins_can_edit_and_delete_published_assistants(
    member_user: MockUser, shared_space: MockSpace
):
    assistant = MagicMock(published=True)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_edit_assistant(assistant=assistant) is False
    assert viewer.can_delete_assistant(assistant=assistant) is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_edit_assistant(assistant=assistant) is False
    assert editor.can_delete_assistant(assistant=assistant) is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_edit_assistant(assistant=assistant) is True
    assert admin.can_delete_assistant(assistant=assistant) is True


def test_no_one_can_publish_websites_in_personal_space(
    owner_user: MockUser, personal_space: MockSpace
):
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_publish_websites() is False


def test_only_admins_can_publish_websites_in_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_publish_websites() is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_publish_websites() is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_publish_websites() is True


def test_only_admins_can_edit_and_delete_published_websites(
    member_user: MockUser, shared_space: MockSpace
):
    website = MagicMock(published=True)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_edit_website(website=website) is False
    assert viewer.can_delete_website(website=website) is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_edit_website(website=website) is False
    assert editor.can_delete_website(website=website) is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_edit_website(website=website) is True
    assert admin.can_delete_website(website=website) is True


def test_no_one_can_publish_groups_in_personal_space(
    owner_user: MockUser, personal_space: MockSpace
):
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_publish_groups() is False


def test_only_admins_can_publish_groups_in_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_publish_groups() is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_publish_groups() is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_publish_groups() is True


def test_only_admins_can_edit_and_delete_published_groups(
    member_user: MockUser, shared_space: MockSpace
):
    group = MagicMock(published=True)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_edit_group(group=group) is False
    assert viewer.can_delete_group(group=group) is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_edit_group(group=group) is False
    assert editor.can_delete_group(group=group) is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_edit_group(group=group) is True
    assert admin.can_delete_group(group=group) is True


def test_no_one_can_publish_services_in_personal_space(
    owner_user: MockUser, personal_space: MockSpace
):
    owner_user.modules.append(Modules.INTRIC_APPLICATIONS)
    actor = SpaceActor(owner_user, personal_space, None)
    assert actor.can_publish_services() is False


def test_only_admins_can_publish_services_in_shared_space(
    member_user: MockUser, shared_space: MockSpace
):
    member_user.modules.append(Modules.INTRIC_APPLICATIONS)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_publish_services() is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_publish_services() is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_publish_services() is True


def test_only_admins_can_edit_and_delete_published_services(
    member_user: MockUser, shared_space: MockSpace
):
    member_user.modules.append(Modules.INTRIC_APPLICATIONS)
    service = MagicMock(published=True)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)
    assert viewer.can_edit_service(service=service) is False
    assert viewer.can_delete_service(service=service) is False

    editor = SpaceActor(member_user, shared_space, MockSpaceRole.EDITOR)
    assert editor.can_edit_service(service=service) is False
    assert editor.can_delete_service(service=service) is False

    admin = SpaceActor(member_user, shared_space, MockSpaceRole.ADMIN)
    assert admin.can_edit_service(service=service) is True
    assert admin.can_delete_service(service=service) is True


def test_viewers_can_only_read_published_resources(
    member_user: MockUser, shared_space: MockSpace
):
    resource = MagicMock(published=False)
    member_user.modules.append(Modules.INTRIC_APPLICATIONS)
    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)

    assert viewer.can_read_assistant(assistant=resource) is False
    assert viewer.can_read_app(app=resource) is False
    assert viewer.can_read_group(group=resource) is False
    assert viewer.can_read_service(service=resource) is False
    assert viewer.can_read_website(website=resource) is False

    # Test with published resources
    published_resource = MagicMock(published=True)

    assert viewer.can_read_assistant(assistant=published_resource) is True
    assert viewer.can_read_app(app=published_resource) is True
    assert viewer.can_read_group(group=published_resource) is True
    assert viewer.can_read_service(service=published_resource) is True
    assert viewer.can_read_website(website=published_resource) is True


def test_viewers_can_not_edit_resource(member_user: MockUser, shared_space: MockSpace):
    resource = MagicMock(published=False)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)

    assert viewer.can_edit_assistant(assistant=resource) is False
    assert viewer.can_edit_app(app=resource) is False
    assert viewer.can_edit_group(group=resource) is False
    assert viewer.can_edit_service(service=resource) is False
    assert viewer.can_edit_website(website=resource) is False


def test_viewers_can_not_delete_resource(
    member_user: MockUser, shared_space: MockSpace
):
    resource = MagicMock(published=False)

    viewer = SpaceActor(member_user, shared_space, MockSpaceRole.VIEWER)

    assert viewer.can_delete_assistant(assistant=resource) is False
    assert viewer.can_delete_app(app=resource) is False
    assert viewer.can_delete_group(group=resource) is False
    assert viewer.can_delete_service(service=resource) is False
    assert viewer.can_delete_website(website=resource) is False
