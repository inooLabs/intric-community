# Copyright (c) 2025 Sundsvalls Kommun
#
# Licensed under the MIT License.
from typing import TYPE_CHECKING, Optional

from intric.group_chat.domain.entities.group_chat import GroupChat, GroupChatAssistant

if TYPE_CHECKING:
    from intric.assistants.assistant import Assistant
    from intric.database.tables.group_chats_table import (
        GroupChatsAssistantsMapping,
        GroupChatsTable,
    )


class GroupChatAssistantFactory:
    @classmethod
    def create_entity(
        cls,
        assistant: "Assistant",
        group_chat_assistant: "GroupChatsAssistantsMapping",
    ) -> "GroupChatAssistant":
        # Create a GroupChatAssistant by extending the base Assistant
        return GroupChatAssistant(
            assistant=assistant,
            user_description=group_chat_assistant.user_description,
        )


class GroupChatFactory:
    @classmethod
    def create_entity(
        cls,
        group_chat: "GroupChatsTable",
        assistants: Optional[list[GroupChatAssistant]] = [],
    ) -> GroupChat:
        return GroupChat(
            created_at=group_chat.created_at,
            updated_at=group_chat.updated_at,
            id=group_chat.id,
            user_id=group_chat.user_id,
            space_id=group_chat.space_id,
            name=group_chat.name,
            assistants=assistants,
            allow_mentions=group_chat.allow_mentions,
            show_response_label=group_chat.show_response_label,
            published=group_chat.published,
            insight_enabled=group_chat.insight_enabled,
        )

    @classmethod
    def create_group_chat_from_db(
        cls,
        group_chat_db: "GroupChatsTable",
        assistants: list["Assistant"],
    ) -> GroupChat:
        group_chat_assistants = []
        for group_chat_assistant in group_chat_db.group_chat_assistants:
            assistant = next(
                (
                    assistant
                    for assistant in assistants
                    if assistant.id == group_chat_assistant.assistant_id
                )
            )
            group_chat_assistants.append(
                GroupChatAssistant(
                    assistant=assistant,
                    user_description=group_chat_assistant.user_description,
                )
            )

        return GroupChat(
            created_at=group_chat_db.created_at,
            updated_at=group_chat_db.updated_at,
            id=group_chat_db.id,
            user_id=group_chat_db.user_id,
            space_id=group_chat_db.space_id,
            name=group_chat_db.name,
            assistants=group_chat_assistants,
            allow_mentions=group_chat_db.allow_mentions,
            show_response_label=group_chat_db.show_response_label,
            published=group_chat_db.published,
            insight_enabled=group_chat_db.insight_enabled,
            metadata_json=group_chat_db.metadata_json,
        )
