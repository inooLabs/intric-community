from typing import TYPE_CHECKING, Optional

from intric.main.config import SETTINGS
from intric.main.models import ResourcePermission
from intric.modules.module import Modules
from intric.roles.permissions import Permission
from intric.spaces.api.space_models import SpaceRole

if TYPE_CHECKING:
    from intric.assistants.assistant import Assistant
    from intric.groups.group import GroupInDB
    from intric.services.service import Service
    from intric.spaces.space import Space
    from intric.users.user import UserInDB
    from intric.websites.website_models import Website

    if SETTINGS.using_intric_proprietary:
        from intric_prop.apps.apps.app import App


# FIXME: The complexity of this class will skyrocket if not tended to.
# The next time we want to add a permission check, we should refactor this.
# The issue is that all of the different `can`-methods are very hard to
# parse and understand.
class SpaceActor:
    def __init__(self, user: "UserInDB", space: "Space", role: Optional["SpaceRole"]):
        self.user = user
        self.space = space
        self.role = role

    def _is_owner(self):
        return self.user.id == self.space.user_id

    def _is_admin(self):
        return self.role == SpaceRole.ADMIN

    def _is_editor(self):
        return self.role == SpaceRole.EDITOR

    def _is_member(self):
        return self.role is not None

    def _is_owner_or_member(self):
        if self.space.is_personal():
            return self._is_owner()

        return self._is_member()

    def can_read_space(self):
        return self._is_owner_or_member()

    def can_edit_space(self):
        if self.space.is_personal():
            # No one can edit the personal space
            return False

        return self._is_admin()

    def can_delete_space(self):
        # Same rules as for edit
        return self.can_edit_space()

    def can_read_members(self):
        if self.space.is_personal():
            return False

        return self._is_editor() or self._is_admin()

    def can_read_default_assistant(self):
        return self._is_owner_or_member()

    def can_edit_default_assistant(self):
        if self.space.is_personal():
            return self._is_owner()

        return self._is_admin()

    def can_read_assistants(self):
        if self.space.is_personal():
            return Permission.ASSISTANTS in self.user.permissions and self._is_owner()

        return self._is_member()

    def can_create_assistants(self):
        if self.space.is_personal():
            return Permission.ASSISTANTS in self.user.permissions and self._is_owner()

        return self._is_editor() or self._is_admin()

    def can_read_assistant(self, assistant: "Assistant"):
        if assistant.published:
            return self._is_member()

        return self.can_create_assistants()

    def can_edit_assistant(self, assistant: "Assistant"):
        if assistant.published:
            return self.can_read_assistants() and self._is_admin()

        return self.can_create_assistants()

    def can_delete_assistant(self, assistant: "Assistant"):
        # Same permission as for editing
        return self.can_edit_assistant(assistant=assistant)

    def can_read_prompts_of_assistant(self, assistant: "Assistant"):
        # Same permission as for editing
        return self.can_edit_assistant(assistant=assistant)

    def can_publish_assistants(self):
        if self.space.is_personal():
            return False

        return self._is_admin()

    def can_read_apps(self):
        if not SETTINGS.using_intric_proprietary or not SETTINGS.using_apps:
            # Apps is a proprietary feature
            return False

        return self._is_owner_or_member()

    def can_create_apps(self):
        if not SETTINGS.using_intric_proprietary or not SETTINGS.using_apps:
            # Apps is a proprietary feature
            return False

        if self.space.is_personal():
            return self._is_owner()

        return self._is_editor() or self._is_admin()

    def can_read_app(self, app: "App"):
        if app.published:
            return self._is_member()

        return self.can_create_apps()

    def can_edit_app(self, app: "App"):
        if app.published:
            return self.can_read_apps() and self._is_admin()

        # Else, same permission as for creating
        return self.can_create_apps()

    def can_delete_app(self, app: "App"):
        # Same permission as for editing
        return self.can_edit_app(app=app)

    def can_read_prompts_of_app(self, app: "App"):
        # Same permission as for editing
        return self.can_edit_app(app=app)

    def can_publish_apps(self):
        # Same permission as for publishing assistants
        return self.can_read_apps() and self.can_publish_assistants()

    def can_read_groups(self):
        if self.space.is_personal():
            return self._is_owner() and Permission.COLLECTIONS in self.user.permissions

        return self._is_editor() or self._is_admin()

    def can_create_groups(self):
        # Same permission as for reading
        return self.can_read_groups()

    def can_read_group(self, group: "GroupInDB"):
        if group.published:
            return self._is_member()

        # Else, same permission as for reading groups
        return self.can_read_groups()

    def can_edit_group(self, group: "GroupInDB"):
        if group.published:
            return self._is_admin()

        # Else, same permission as for reading groups
        return self.can_read_groups()

    def can_delete_group(self, group: "GroupInDB"):
        # Same permission as for editing
        return self.can_edit_group(group=group)

    def can_publish_groups(self):
        # Same permission as for publishing assistants
        return self.can_read_groups() and self.can_publish_assistants()

    def can_read_websites(self):
        if not SETTINGS.using_intric_proprietary:
            # Websites is a proprietary feature
            return False

        if self.space.is_personal():
            return self._is_owner() and Permission.WEBSITES in self.user.permissions

        return self._is_editor() or self._is_admin()

    def can_create_websites(self):
        # Same permission as for reading
        return self.can_read_websites()

    def can_read_website(self, website: "Website"):
        if website.published:
            return self._is_member()

        return self.can_read_websites()

    def can_edit_website(self, website: "Website"):
        if website.published:
            return self.can_read_websites() and self._is_admin()

        # Else, same permission as for creating
        return self.can_read_websites()

    def can_delete_website(self, website: "Website"):
        # Same permission as for editing
        return self.can_edit_website(website=website)

    def can_publish_websites(self):
        # Same permission as for publishing assistants
        return self.can_read_websites() and self.can_publish_assistants()

    def can_read_services(self):
        if Modules.INTRIC_APPLICATIONS not in self.user.modules:
            return False

        if self.space.is_personal():
            return self._is_owner() and Permission.SERVICES in self.user.permissions

        return self._is_member()

    def can_create_services(self):
        if Modules.INTRIC_APPLICATIONS not in self.user.modules:
            return False

        if self.space.is_personal():
            return self._is_owner() and Permission.SERVICES in self.user.permissions

        return self._is_editor() or self._is_admin()

    def can_read_service(self, service: "Service"):
        if service.published:
            return self.can_read_services() and self._is_member()

        return self.can_create_services()

    def can_edit_service(self, service: "Service"):
        if service.published:
            return self.can_read_services() and self._is_admin()

        # Same permission as for creating
        return self.can_create_services()

    def can_delete_service(self, service: "Service"):
        # Same permission as for editing
        return self.can_edit_service(service=service)

    def can_publish_services(self):
        # Same permission as for publishing assistants
        return self.can_read_services() and self.can_publish_assistants()

    def _get_resource_permissions(
        self, can_edit: bool, can_delete: bool, can_publish: bool
    ):
        permissions = []

        if can_edit:
            permissions.append(ResourcePermission.EDIT)

        if can_delete:
            permissions.append(ResourcePermission.DELETE)

        if can_publish:
            permissions.append(ResourcePermission.PUBLISH)

        return permissions

    def get_assistant_permissions(self, assistant: "Assistant"):
        return self._get_resource_permissions(
            self.can_edit_assistant(assistant=assistant),
            self.can_delete_assistant(assistant=assistant),
            self.can_publish_assistants(),
        )

    def get_app_permissions(self, app: "App"):
        return self._get_resource_permissions(
            self.can_edit_app(app=app),
            self.can_delete_app(app=app),
            self.can_publish_apps(),
        )

    def get_group_permissions(self, group: "GroupInDB"):
        return self._get_resource_permissions(
            self.can_edit_group(group=group),
            self.can_delete_group(group=group),
            self.can_publish_groups(),
        )

    def get_website_permissions(self, website: "Website"):
        return self._get_resource_permissions(
            self.can_edit_website(website=website),
            self.can_delete_website(website=website),
            self.can_publish_websites(),
        )

    def get_service_permissions(self, service: "Service"):
        return self._get_resource_permissions(
            self.can_edit_service(service=service),
            self.can_delete_service(service=service),
            self.can_publish_services(),
        )
