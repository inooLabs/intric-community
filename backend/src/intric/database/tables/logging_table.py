# MIT License

from sqlalchemy import UUID, Column, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import registry

from intric.database.tables.base_class import Base

mapper_registry = registry()


def create_logging_table(metadata_obj):
    table = Table(
        "logging",
        metadata_obj,
        Column(
            "id",
            UUID,
            primary_key=True,
            server_default=func.gen_random_uuid(),
        ),
        Column("context", String),
        Column("model_kwargs", JSONB),
        Column("json_body", JSONB),
    )

    class Logging:
        pass

    mapper_registry.map_imperatively(Logging, table)

    return Logging


logging_table = create_logging_table(Base.metadata)
