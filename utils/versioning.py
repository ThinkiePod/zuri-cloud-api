from enum import Enum

class APIVersion(Enum):
    V1 = "v1"
    V2 = "v2"

CURRENT_VERSION = APIVersion.V2
DEPRECATED_VERSIONS = [APIVersion.V1]

def is_deprecated(version: APIVersion) -> bool:
    return version in DEPRECATED_VERSIONS