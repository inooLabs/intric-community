# MIT License

from typing import Optional

from pydantic import BaseModel, ConfigDict, Json

from intric.main.models import InDB


class LoggingDetails(BaseModel):
    context: Optional[str] = None
    model_kwargs: dict
    json_body: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


class LoggingDetailsInDB(LoggingDetails, InDB):
    pass


class LoggingDetailsPublic(LoggingDetails):
    json_body: Json
