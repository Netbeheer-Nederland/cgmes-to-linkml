"""
TODO:

- Absolute URIs maken overal.

"""

import json
import sys
from pathlib import Path
from pprint import pprint
from typing import Optional
from xml.etree import ElementTree

import xmltodict
import yaml
from pydantic import BaseModel, Field, PrivateAttr

### Variables and Vocabularies.

N = sys.maxsize
XML_BASE = "http://iec.ch/TC57/CIM100"

class RDF:
    _ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    Property = _ns + "Property"

class RDFS:
    _ns = "http://www.w3.org/2000/01/rdf-schema#"
    Class = _ns + "Class"

class TC57UML:
    _ns = "http://iec.ch/TC57/NonStandard/UML#"
    enumeration = _ns + "enumeration"

### CIM RDF Schema dataclasses.

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

### LinkML dataclasses.

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

### Parsing functions.

def parse_namespaces(prof_fp):
    tree_iter = ElementTree.iterparse(prof_fp, events=["start-ns"])

    return {ns[1]: ns[0] for _, ns in tree_iter}  # {uri: prefix}


def parse_ontology_declaration(prof):
    return prof["rdf:RDF"]["rdf:Description"][0]


def parse_profile_declaration(prof):
    return prof["rdf:RDF"]["rdf:Description"][1]


def _read_stereotype(stereotype):
    match stereotype:
        case dict():
            return stereotype.get("@rdf:resource") or stereotype.get("#text")
        case str():
            return stereotype


def _read_label(label):
    # Currently only English language tags are used, so we're not looking for anything else.
    return label["#text"]


def _read_comment(comment):
    # Currently only English language tags are used, so we're not looking for anything else.
    if comment is not None:
        return comment["#text"]


def _get_stereotypes(resource) -> Optional[list]:
    stereotype_el = resource.get("cims:stereotype")
    match stereotype_el:
        case list():
            return list(map(_read_stereotype, stereotype_el))
        case None:
            return []
        case _:
            return [_read_stereotype(stereotype_el)]


def _map_multiplicity(value):
    return {
        "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:0..1": (0, 1),
        "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:0..2": (0, 2),
        "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:0..n": (0, N),
        "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:1": (1, 1),
        "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:1..1": (1, 1),
        "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:1..n": (1, N),
    }[value]

def _get_absolute_iri(uri, base_uri=XML_BASE):
    # Assumption that seems safe for now: relative URIs start with `#`.
    if uri.startswith("#"):
        return base_uri + uri
    else:
        return uri


def parse_property(resource):
    return CIMRDFSProperty(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        label=_read_label(resource["rdfs:label"]),
        domain=resource["rdfs:domain"]["@rdf:resource"],
        multiplicity=_map_multiplicity(resource["cims:multiplicity"]["@rdf:resource"]),
        stereotypes=_get_stereotypes(resource),
        comment=_read_comment(resource.get("rdfs:comment")),
        range=resource.get("rdfs:range", {}).get("@rdf:resource"),
        datatype=resource.get("cims:dataType", {}).get("@rdf:resource"),
        is_fixed=resource.get("cims:isFixed", {}).get("#text"),
    )


def parse_class(resource) -> CIMRDFSClass:
    return CIMRDFSClass(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        label=_read_label(resource["rdfs:label"]),
        stereotypes=_get_stereotypes(resource),
        attributes={},
        subclass_of=resource.get("rdfs:subClassOf", {}).get("@rdf:resource"),
        comment=_read_comment(resource["rdfs:comment"]),
        belongs_to_category=resource["cims:belongsToCategory"]["@rdf:resource"],
    )


def parse_enumeration(resource) -> CIMRDFSEnumeration:
    return CIMRDFSEnumeration(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        values={},
        label=_read_label(resource["rdfs:label"]),
        stereotypes=_get_stereotypes(resource),
        comment=_read_comment(resource["rdfs:comment"]),
    )


def parse_enum_value(resource) -> CIMRDFSEnumValue:
    return CIMRDFSEnumValue(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        label=_read_label(resource["rdfs:label"]),
        type=resource["rdf:type"]["@rdf:resource"],
        stereotypes=["enum"],
    )


def bind_properties_to_classes(classes, enums, properties):  # TODO: Rename such that it describes everything it does.
    for property_iri, property_ in properties.items():
        class_ = classes[property_.domain]
        class_.attributes[property_iri] = property_

        if property_.range:
            try:
                property_.range = classes[property_.range]
            except KeyError:
                property_.range = enums[property_.range]


def bind_enum_values_to_enums(enums, enum_values):
    for enum_value_iri, enum_value in enum_values.items():
        enum = enums[enum_value.type]
        enum.values[enum_value_iri] = enum_value


def parse_resources(prof):
    resources = prof["rdf:RDF"]["rdf:Description"][2:]

    classes = {}
    properties = {}
    enums = {}
    enum_values = {}

    for resource in resources:
        iri = resource["@rdf:about"]
        type_ = resource["rdf:type"]["@rdf:resource"]
        stereotypes = _get_stereotypes(resource)

        match type_:
            case RDFS.Class:
                if TC57UML.enumeration in stereotypes:
                    enums[iri] = parse_enumeration(resource)
                else:
                    classes[iri] = parse_class(resource)
            case RDF.Property:
                properties[iri] = parse_property(resource)
            case _:
                if "enum" in stereotypes:
                    enum_values[iri] = parse_enum_value(resource)

    bind_enum_values_to_enums(enums, enum_values)
    bind_properties_to_classes(classes, enums, properties)

    return classes, enums


### LinkML generation.

def _map_datatype(value):
    return ""


def gen_attribute(property_: CIMRDFSProperty) -> LinkMLAttribute:
    if property_.datatype:
        range_ = _map_datatype(property_.datatype)
    else:
        range_ = property_.range.label

    return LinkMLAttribute(
        name=property_.label,
        slot_uri=property_.iri,
        range=range_,
        multivalued=True if property_.multiplicity[1] > 1 else False,
        required=True if property_.multiplicity[0] > 0 else False,
        description=property_.comment,
    )


def gen_class(class_: CIMRDFSClass, super_class: Optional[str] = None) -> LinkMLClass:
    return LinkMLClass(
        _name=class_.label,
        class_uri=class_.iri,
        attributes={attr.label: gen_attribute(attr) for attr in class_.attributes.values()},
        is_a=super_class,
        description=class_.comment,
    )


def write_classes(classes: dict[str, CIMRDFSClass]):
    for class_iri, class_ in classes.items():
        super_class_label = classes[class_iri].label
        linkml_class = gen_class(class_, super_class_label)
        
        # print(linkml_class.model_dump_json())
        print(yaml.safe_dump(linkml_class.model_dump(mode="json"), sort_keys=False))
        break


if __name__ == "__main__":
    tests_dir = Path("tests")
    eq_prof_fp = tests_dir / "data" / "IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf"
    eq_prof_nss = parse_namespaces(eq_prof_fp)
    eq_prof = xmltodict.parse(
        eq_prof_fp.read_text(),
        process_namespaces=True,
        namespaces=eq_prof_nss,
        attr_prefix="@",
        cdata_key="#text",
    )

    # print(parse_ontology_declaration(eq_prof))
    classes, enums = parse_resources(eq_prof)
    write_classes(classes)
