from typing import Optional

from pydantic import BaseModel, PrivateAttr


class LinkMLAttribute(BaseModel):
    _name: str = PrivateAttr(None)
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
    attributes: Optional[dict[str, LinkMLAttribute]] = None
    is_a: Optional[str] = None
    description: Optional[str] = None


class LinkMLSchema(BaseModel):
    id: str
    name: str
    description: str
    prefixes: dict[str, str]
    imports: list[str]
    default_curi_maps: list[str]
    default_range: Optional[str] = None
    default_prefix: Optional[str] = None
    classes: Optional[dict] = None
    enums: Optional[dict] = None
    slots: Optional[dict] = None


class LinkMLEnumValue(BaseModel):
    _name: str = PrivateAttr(...)
    description: Optional[str] = None
    meaning: Optional[str] = None


class LinkMLEnum(BaseModel):
    _name: str = PrivateAttr(...)
    permissible_values: dict[str, LinkMLEnumValue]
    enum_uri: Optional[str] = None
