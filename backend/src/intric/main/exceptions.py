from enum import Enum


class ErrorCodes(int, Enum):
    NOT_FOUND = 9000
    UNAUTHORIZED = 9001
    UNSUPPORTED_MODEL = 9002
    QUERY_ERROR = 9003
    UNIQUE_USER_ERROR = 9004
    AUTHENTICATION_ERROR = 9005
    USER_NOT_CREATED = 9006
    BAD_REQUEST = 9007
    QUOTA_EXCEEDED = 9008
    UNIQUE_ERROR = 9009
    OPENAI_ERROR = 9010
    CLAUDE_ERROR = 9011
    VALIDATION_ERROR = 9012
    PYDANTIC_PARSE_ERROR = 9013
    FILE_NOT_SUPPORTED = 9014
    FILE_TOO_LARGE = 9015
    CHUNK_EMBEDDING_MISMATCH = 9016
    NAME_COLLISION = 9017
    PROVISIONING_NOT_ENABLED = 9018
    USER_INACTIVE = 9019
    NO_MODEL_SELECTED = 9020
    CRAWL_ALREADY_RUNNING = 9021


class NotFoundException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


class UnsupportedModelException(Exception):
    pass


class QueryException(Exception):
    pass


class UniqueUserException(Exception):
    pass


class AuthenticationException(Exception):
    pass


class BadRequestException(Exception):
    pass


class QuotaExceededException(Exception):
    pass


class UniqueException(Exception):
    pass


class OpenAIException(Exception):
    pass


class ClaudeException(Exception):
    pass


class ValidationException(Exception):
    pass


class PydanticParseError(Exception):
    pass


class NotReadyException(Exception):
    pass


class FileNotSupportedException(Exception):
    pass


class FileTooLargeException(Exception):
    pass


class ChunkEmbeddingMisMatchException(Exception):
    pass


class CrawlerException(Exception):
    pass


class NameCollisionException(Exception):
    pass


class UserNotCreatedInIntricError(Exception):
    pass


class ProvisioningNotAllowed(Exception):
    pass


class UserInactiveException(Exception):
    pass


class NoModelSelectedException(Exception):
    pass


class CrawlAlreadyRunningException(Exception):
    pass


# Map exceptions to response codes
# Set message to None to use the internal message
# Set error codes in the range 9000 - 9999
EXCEPTION_MAP = {
    NotFoundException: (404, "Not found", ErrorCodes.NOT_FOUND),
    UnauthorizedException: (403, None, ErrorCodes.UNAUTHORIZED),
    UnsupportedModelException: (400, None, ErrorCodes.UNSUPPORTED_MODEL),
    QueryException: (400, None, ErrorCodes.QUERY_ERROR),
    UniqueUserException: (400, None, ErrorCodes.UNIQUE_USER_ERROR),
    AuthenticationException: (401, "Unauthenticated", ErrorCodes.AUTHENTICATION_ERROR),
    UserNotCreatedInIntricError: (
        401,
        "User is not created",
        ErrorCodes.USER_NOT_CREATED,
    ),
    BadRequestException: (400, None, ErrorCodes.BAD_REQUEST),
    QuotaExceededException: (403, None, ErrorCodes.QUOTA_EXCEEDED),
    UniqueException: (400, None, ErrorCodes.UNIQUE_ERROR),
    OpenAIException: (503, None, ErrorCodes.OPENAI_ERROR),
    ClaudeException: (503, None, ErrorCodes.CLAUDE_ERROR),
    ValidationException: (422, None, ErrorCodes.VALIDATION_ERROR),
    PydanticParseError: (500, None, ErrorCodes.PYDANTIC_PARSE_ERROR),
    FileNotSupportedException: (415, None, ErrorCodes.FILE_NOT_SUPPORTED),
    FileTooLargeException: (413, None, ErrorCodes.FILE_TOO_LARGE),
    ChunkEmbeddingMisMatchException: (
        500,
        "Something went wrong.",
        ErrorCodes.CHUNK_EMBEDDING_MISMATCH,
    ),
    NameCollisionException: (400, None, ErrorCodes.NAME_COLLISION),
    ProvisioningNotAllowed: (403, None, ErrorCodes.PROVISIONING_NOT_ENABLED),
    UserInactiveException: (403, None, ErrorCodes.USER_INACTIVE),
    NoModelSelectedException: (400, None, ErrorCodes.NO_MODEL_SELECTED),
    CrawlAlreadyRunningException: (429, None, ErrorCodes.CRAWL_ALREADY_RUNNING),
}
