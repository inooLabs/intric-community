from typing import TYPE_CHECKING

from intric.actors.actors.space_actor import SpaceActor

if TYPE_CHECKING:
    from intric.spaces.space import Space
    from intric.users.user import UserInDB


class ActorFactory:
    @staticmethod
    def create_space_actor(user: "UserInDB", space: "Space"):
        space_member = space.members.get(user.id)
        role = space_member.role if space_member is not None else None

        return SpaceActor(user=user, space=space, role=role)
