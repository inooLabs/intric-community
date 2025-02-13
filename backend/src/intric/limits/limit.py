from pydantic import BaseModel


class FormatLimit(BaseModel):
    mimetype: str
    size: int
    extensions: list[str]
    vision: bool


class InfoBlobLimits(BaseModel):
    formats: list[FormatLimit]


class AttachmentLimits(BaseModel):
    formats: list[FormatLimit]
    max_in_question: int


class Limits(BaseModel):
    info_blobs: InfoBlobLimits
    attachments: AttachmentLimits
