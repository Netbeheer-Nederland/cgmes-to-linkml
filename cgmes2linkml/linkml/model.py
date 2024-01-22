from typing import Optional

from pydantic import BaseModel, PrivateAttr


class LinkMLAttribute(BaseModel):
    _name: str = PrivateAttr(...)
    slot_uri: str
    range: str
    multivalued: bool
    required: bool
    description: Optional[str] = None
    # identifier: bool = False
    # inlined_as_list: bool = False
    # inverse: Optional[str] = None


class LinkMLClass(BaseModel):
    _name: str = PrivateAttr(...)
    class_uri: str
    attributes: dict[str, LinkMLAttribute]
    is_a: Optional[str] = None
    description: Optional[str] = None
