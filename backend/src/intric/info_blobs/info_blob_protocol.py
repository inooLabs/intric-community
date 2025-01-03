from typing import Type

from intric.info_blobs.info_blob import (
    InfoBlobInDB,
    InfoBlobMetadata,
    InfoBlobPublic,
    InfoBlobPublicNoText,
)


def to_info_blob_public(blob: InfoBlobInDB):
    return to_model(blob, InfoBlobPublic)


def to_info_blob_public_no_text(blob: InfoBlobInDB):
    return to_model(blob, InfoBlobPublicNoText)


def to_model(blob: InfoBlobInDB, public_model: Type[InfoBlobPublicNoText]):
    return public_model(
        **blob.model_dump(),
        metadata=InfoBlobMetadata(**blob.model_dump()),
    )
