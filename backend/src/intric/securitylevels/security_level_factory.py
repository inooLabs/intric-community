# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.

from fastapi import Depends

from intric.main.container.container import Container
from intric.server.dependencies.container import get_container


def get_security_level_service(container: Container = Depends(get_container(with_user=True))):
    return container.security_level_service()


def get_security_level_service_from_assistant_api_key(
    container: Container = Depends(
        get_container(with_user_from_assistant_api_key=True)
    ),
):
    return container.security_level_service()
