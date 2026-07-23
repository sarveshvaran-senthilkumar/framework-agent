from typing import Any

from pydantic import BaseModel


class MappingRequest(BaseModel):
    """Generic JSON payload accepted by the mapper."""

    payload: dict[str, Any]
