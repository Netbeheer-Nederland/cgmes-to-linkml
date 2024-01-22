from typing import Optional

from pydantic import BaseModel


IRI = str


class CIMRDFSResource(BaseModel):
    iri: IRI
    label: str
    stereotypes: list[str]
    comment: Optional[str] = None


class CIMRDFSProperty(CIMRDFSResource):
    domain: IRI
    multiplicity: tuple[int, int]
    range: Optional[IRI] = None
    datatype: Optional[str] = None
    is_fixed: Optional[str] = None


class CIMRDFSClass(CIMRDFSResource):
    attributes: dict[IRI, CIMRDFSProperty]
    subclass_of: Optional[IRI] = None
    belongs_to_category: Optional[str] = None


class CIMRDFSEnumValue(CIMRDFSResource):
    type: IRI


class CIMRDFSEnumeration(CIMRDFSResource):
    values: dict[str, CIMRDFSEnumValue]


class CGMESOntologyDeclaration(BaseModel):
    keyword: str
    version_info: str
    creator: str
    description: str
    identifier: str
    # issued: datetime
    # modified: datetime
    language: str
    publisher: str
    title: str


class CGMESProfileDeclaration(CIMRDFSResource):
    type: IRI
