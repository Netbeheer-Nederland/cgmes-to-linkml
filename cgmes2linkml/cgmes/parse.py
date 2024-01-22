import sys
from typing import Optional
from xml.etree import ElementTree

import xmltodict

from cgmes2linkml.cgmes.model import (
    CIMRDFSClass,
    CIMRDFSProperty,
    CIMRDFSEnumeration,
    CIMRDFSEnumValue,
    CGMESOntologyDeclaration,
    CGMESProfileDeclaration,
)
from cgmes2linkml.cgmes.vocabulary import RDF, RDFS, TC57UML

N = sys.maxsize
XML_BASE = "http://iec.ch/TC57/CIM100"


def _parse_namespaces(prof_fp):
    tree_iter = ElementTree.iterparse(prof_fp, events=["start-ns"])

    return {ns[1]: ns[0] for _, ns in tree_iter}  # {uri: prefix}


def _parse_ontology_declaration(header):
    # Currently only English language tags are used, so we're not looking for anything else.
    return CGMESOntologyDeclaration(
        keyword=header["dcat:keyword"],
        version_info=header["owl:versionInfo"]["#text"],
        creator=header["dct:creator"]["#text"],
        description=header["dct:description"]["#text"],
        identifier=header["dct:identifier"],
        # issued: datetime
        # modified: datetime
        language=header["dct:language"],
        publisher=header["dct:publisher"]["#text"],
        title=header["dct:title"]["#text"],
    )


def _parse_profile_declaration(resource):
    # Currently only English language tags are used, so we're not looking for anything else.
    return CGMESProfileDeclaration(
        iri=resource["@rdf:about"],
        label=_read_label(resource["rdfs:label"]),
        type=resource["rdf:type"]["@rdf:resource"],
        stereotypes=[],
        comment=_read_comment(resource.get("rdfs:comment")),
    )


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


def _parse_property(resource):
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


def _parse_class(resource) -> CIMRDFSClass:
    return CIMRDFSClass(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        label=_read_label(resource["rdfs:label"]),
        stereotypes=_get_stereotypes(resource),
        attributes={},
        subclass_of=resource.get("rdfs:subClassOf", {}).get("@rdf:resource"),
        comment=_read_comment(resource["rdfs:comment"]),
        belongs_to_category=resource["cims:belongsToCategory"]["@rdf:resource"],
    )


def _parse_enumeration(resource) -> CIMRDFSEnumeration:
    return CIMRDFSEnumeration(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        values={},
        label=_read_label(resource["rdfs:label"]),
        stereotypes=_get_stereotypes(resource),
        comment=_read_comment(resource["rdfs:comment"]),
    )


def _parse_enum_value(resource) -> CIMRDFSEnumValue:
    return CIMRDFSEnumValue(
        iri=_get_absolute_iri(resource["@rdf:about"]),
        label=_read_label(resource["rdfs:label"]),
        type=resource["rdf:type"]["@rdf:resource"],
        stereotypes=["enum"],
    )


def _bind_properties_to_classes(classes, enums, properties):
    # TODO: Rename such that it describes everything it does.
    # TODO: Split up in more functions and clean up.
    for property_iri, property_ in properties.items():
        class_ = classes[property_.domain]
        class_.attributes[property_iri] = property_

        if property_.datatype:
            if datatype_class := classes.get(property_.datatype):
                property_.is_primitive = "Primitive" in datatype_class.stereotypes
                property_.datatype = classes[property_.datatype]
            else:
                property_.is_primitive = False
                try:
                    property_.datatype = classes[property_.datatype]
                except KeyError:
                    property_.datatype = enums[property_.datatype]
        elif property_.range:
            property_.is_primitive = False
            try:
                property_.range = classes[property_.range]
            except KeyError:
                property_.range = enums[property_.range]


def _bind_enum_values_to_enums(enums, enum_values):
    for enum_value_iri, enum_value in enum_values.items():
        enum = enums[enum_value.type]
        enum.values[enum_value_iri] = enum_value


def _parse_profile_as_dict(prof_fp, namespaces):
    prof = xmltodict.parse(
        prof_fp.read_text(),
        process_namespaces=True,
        namespaces=namespaces,
        attr_prefix="@",
        cdata_key="#text",
    )
    return prof


def _parse_model(resources):
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
                    enums[iri] = _parse_enumeration(resource)
                else:
                    classes[iri] = _parse_class(resource)
            case RDF.Property:
                properties[iri] = _parse_property(resource)
            case _:
                if "enum" in stereotypes:
                    enum_values[iri] = _parse_enum_value(resource)

    _bind_enum_values_to_enums(enums, enum_values)
    _bind_properties_to_classes(classes, enums, properties)

    return classes, enums


def parse_profile(prof_fp):
    namespaces = _parse_namespaces(prof_fp)
    prof = _parse_profile_as_dict(prof_fp, namespaces)
    ontology_meta = _parse_ontology_declaration(prof["rdf:RDF"]["rdf:Description"][0])
    profile_meta = _parse_profile_declaration(prof["rdf:RDF"]["rdf:Description"][1])
    classes, enums = _parse_model(prof["rdf:RDF"]["rdf:Description"][2:])

    return namespaces, ontology_meta, profile_meta, classes, enums
