from typing import Optional

from pydantic import BaseModel


class RDF:
    _ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    Property = _ns + "Property"


class RDFS:
    _ns = "http://www.w3.org/2000/01/rdf-schema#"
    Class = _ns + "Class"


class TC57UML:
    _ns = "http://iec.ch/TC57/NonStandard/UML#"
    enumeration = _ns + "enumeration"


class CIMRDFSResource(BaseModel):
    iri: str
    label: str
    stereotypes: list[str]
    comment: Optional[str] = None


class CIMRDFSProperty(CIMRDFSResource):
    domain: str
    multiplicity: tuple
    range: Optional[str] = None
    datatype: Optional[str] = None
    is_fixed: Optional[str] = None


class CIMRDFSClass(CIMRDFSResource):
    attributes: dict[str, CIMRDFSProperty]
    subclass_of: Optional[str] = None
    belongs_to_category: Optional[str] = None


class CIMRDFSEnumValue(CIMRDFSResource):
    type: str


class CIMRDFSEnumeration(CIMRDFSResource):
    values: dict[str, CIMRDFSEnumValue]
