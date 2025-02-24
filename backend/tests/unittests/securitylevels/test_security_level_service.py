# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from intric.main.exceptions import BadRequestException, NotFoundException, UnauthorizedException
from intric.roles.permissions import Permission
from intric.securitylevels.security_level import SecurityLevel
from intric.securitylevels.security_level_service import SecurityLevelService
from tests.fixtures import TEST_UUID, TEST_TENANT

TEST_NAME = "test_security_level"
TEST_DESCRIPTION = "A test security level"
TEST_VALUE = 100


@pytest.fixture
def service():
    repo = AsyncMock()
    # Default to no existing security level with any name
    repo.get_by_name_and_tenant.return_value = None

    user = MagicMock()
    user.permissions = []  # Default to no permissions
    user.tenant_id = TEST_TENANT.id

    return SecurityLevelService(
        repo=repo,
        user=user,
    )


@pytest.fixture
def security_level():
    return SecurityLevel(
        id=TEST_UUID,
        name=TEST_NAME,
        description=TEST_DESCRIPTION,
        value=TEST_VALUE,
        tenant_id=TEST_TENANT.id,
        created_at=None,
        updated_at=None,
    )


async def test_create_security_level(service, security_level):
    """Test creating a security level."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.create.return_value = security_level

    # Execute
    result = await service.create_security_level(
        name=TEST_NAME,
        description=TEST_DESCRIPTION,
        value=TEST_VALUE,
    )

    # Assert
    assert result == security_level
    service.repo.create.assert_called_once()


async def test_create_security_level_no_permission(service):
    """Test creating a security level without admin permission."""
    # Setup - no permissions by default

    # Execute & Assert
    with pytest.raises(UnauthorizedException):
        await service.create_security_level(
            name=TEST_NAME,
            description=TEST_DESCRIPTION,
            value=TEST_VALUE,
        )

    service.repo.create.assert_not_called()


async def test_create_security_level_duplicate_name(service, security_level):
    """Test creating a security level with duplicate name."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.get_by_name_and_tenant.return_value = security_level

    # Execute & Assert
    with pytest.raises(BadRequestException):
        await service.create_security_level(
            name=TEST_NAME,
            description=TEST_DESCRIPTION,
            value=TEST_VALUE,
        )

    service.repo.create.assert_not_called()


async def test_get_security_level(service, security_level):
    """Test getting a security level."""
    # Setup
    service.repo.get.return_value = security_level

    # Execute
    result = await service.get_security_level(TEST_UUID)

    # Assert
    assert result == security_level
    service.repo.get.assert_called_once_with(TEST_UUID)


async def test_get_security_level_not_found(service):
    """Test getting a non-existent security level."""
    # Setup
    service.repo.get.return_value = None

    # Execute & Assert
    with pytest.raises(NotFoundException):
        await service.get_security_level(TEST_UUID)


async def test_get_security_level_wrong_tenant(service, security_level):
    """Test getting a security level from wrong tenant."""
    # Setup
    wrong_tenant_level = SecurityLevel(
        id=TEST_UUID,
        name=TEST_NAME,
        description=TEST_DESCRIPTION,
        value=TEST_VALUE,
        tenant_id=uuid4(),  # Different tenant
        created_at=None,
        updated_at=None,
    )
    service.repo.get.return_value = wrong_tenant_level

    # Execute & Assert
    with pytest.raises(NotFoundException):
        await service.get_security_level(TEST_UUID)


async def test_list_security_levels(service, security_level):
    """Test listing security levels."""
    # Setup
    service.repo.list_by_tenant.return_value = [security_level]

    # Execute
    result = await service.list_security_levels()

    # Assert
    assert result == [security_level]
    service.repo.list_by_tenant.assert_called_once_with(TEST_TENANT.id)


async def test_update_security_level(service, security_level):
    """Test updating a security level."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.get.return_value = security_level
    service.repo.update.return_value = security_level

    # Execute
    result = await service.update_security_level(
        id=TEST_UUID,
        name="updated_name",
        description="updated_description",
        value=200,
    )

    # Assert
    assert result == security_level
    service.repo.update.assert_called_once()


async def test_update_security_level_not_found(service):
    """Test updating a non-existent security level."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.get.return_value = None

    # Execute & Assert
    with pytest.raises(NotFoundException):
        await service.update_security_level(
            id=TEST_UUID,
            name="updated_name",
        )

    service.repo.update.assert_not_called()


async def test_update_security_level_wrong_tenant(service, security_level):
    """Test updating a security level from wrong tenant."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    wrong_tenant_level = SecurityLevel(
        id=TEST_UUID,
        name=TEST_NAME,
        description=TEST_DESCRIPTION,
        value=TEST_VALUE,
        tenant_id=uuid4(),  # Different tenant
        created_at=None,
        updated_at=None,
    )
    service.repo.get.return_value = wrong_tenant_level

    # Execute & Assert
    with pytest.raises(NotFoundException):
        await service.update_security_level(
            id=TEST_UUID,
            name="updated_name",
        )

    service.repo.update.assert_not_called()


async def test_update_security_level_no_permission(service, security_level):
    """Test updating a security level without admin permission."""
    # Setup
    service.repo.get.return_value = security_level
    # No permissions by default

    # Execute & Assert
    with pytest.raises(UnauthorizedException):
        await service.update_security_level(
            id=TEST_UUID,
            name="updated_name",
        )

    service.repo.update.assert_not_called()


async def test_update_security_level_duplicate_name(service, security_level):
    """Test updating a security level with duplicate name."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.get.return_value = security_level
    service.repo.get_by_name_and_tenant.return_value = SecurityLevel(
        id=uuid4(),
        name="existing_name",
        value=0,
        tenant_id=TEST_TENANT.id,
    )

    # Execute & Assert
    with pytest.raises(BadRequestException):
        await service.update_security_level(
            id=TEST_UUID,
            name="existing_name",
        )

    service.repo.update.assert_not_called()


async def test_delete_security_level(service, security_level):
    """Test deleting a security level."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.get.return_value = security_level

    # Execute
    await service.delete_security_level(TEST_UUID)

    # Assert
    service.repo.delete.assert_called_once_with(TEST_UUID)


async def test_delete_security_level_not_found(service):
    """Test deleting a non-existent security level."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    service.repo.get.return_value = None

    # Execute & Assert
    with pytest.raises(NotFoundException):
        await service.delete_security_level(TEST_UUID)

    service.repo.delete.assert_not_called()


async def test_delete_security_level_wrong_tenant(service, security_level):
    """Test deleting a security level from wrong tenant."""
    # Setup
    service.user.permissions = [Permission.ADMIN]
    wrong_tenant_level = SecurityLevel(
        id=TEST_UUID,
        name=TEST_NAME,
        description=TEST_DESCRIPTION,
        value=TEST_VALUE,
        tenant_id=uuid4(),  # Different tenant
        created_at=None,
        updated_at=None,
    )
    service.repo.get.return_value = wrong_tenant_level

    # Execute & Assert
    with pytest.raises(NotFoundException):
        await service.delete_security_level(TEST_UUID)

    service.repo.delete.assert_not_called()


async def test_delete_security_level_no_permission(service, security_level):
    """Test deleting a security level without admin permission."""
    # Setup
    service.repo.get.return_value = security_level
    # No permissions by default

    # Execute & Assert
    with pytest.raises(UnauthorizedException):
        await service.delete_security_level(TEST_UUID)

    service.repo.delete.assert_not_called()


async def test_validate_security_level(service, security_level):
    """Test validating security levels."""
    # Setup
    required = SecurityLevel(
        id=uuid4(),
        name="required",
        value=100,
        tenant_id=TEST_TENANT.id,
    )
    provided = SecurityLevel(
        id=uuid4(),
        name="provided",
        value=200,
        tenant_id=TEST_TENANT.id,
    )

    # Execute & Assert
    assert await service.validate_security_level(required, provided) is True

    # Test with lower value
    provided.value = 50
    assert await service.validate_security_level(required, provided) is False

    # Test with different tenant
    provided.value = 200
    provided.tenant_id = uuid4()
    assert await service.validate_security_level(required, provided) is False


async def test_get_highest_security_level(service):
    """Test getting the highest security level value."""
    # Setup
    service.repo.get_highest_value_by_tenant.return_value = TEST_VALUE

    # Execute
    result = await service.get_highest_security_level()

    # Assert
    assert result == TEST_VALUE
    service.repo.get_highest_value_by_tenant.assert_called_once_with(TEST_TENANT.id)
