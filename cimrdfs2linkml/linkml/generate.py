from pathlib import Path
from typing import Optional

from cimrdfs2linkml.cimrdfs.model import (
    CIMRDFSClass,
    CIMRDFSProperty,
    CGMESOntologyDeclaration,
    CGMESProfileDeclaration,
    CIMRDFSEnumeration,
    CIMRDFSEnumValue,
)
from cimrdfs2linkml.linkml.model import LinkMLClass, LinkMLAttribute, LinkMLSchema, LinkMLEnum, LinkMLEnumValue


def _map_to_curie(uri: str, prefix_map: dict[str, str]) -> str:
    for ns_prefix, ns_uri in prefix_map.items():
        try:
            return f"{ns_prefix}:{uri.split(ns_uri)[1]}"
        except IndexError:
            continue
    return uri  # Empy prefix map: do nothing.


def _map_datatype(datatype):
    match datatype.iri.split("#")[-1]:
        case "Float":
            return "float"
        case "Integer":
            return "integer"
        case "DateTime":
            return "date"
        case "String":
            return "string"
        case "Boolean":
            return "boolean"
        case "Decimal":
            return "double"  # Is this right?
        case "MonthDay":
            return "date"  # Is this right?
        case "Date":
            return "date"
        case _:
            raise TypeError(f"Data type `{datatype.label}` is not a CIM Primitive.")


def _generate_attribute(property_: CIMRDFSProperty, prefixes) -> LinkMLAttribute:
    if property_.is_primitive:
        range_ = _map_datatype(property_.datatype)
    elif property_.datatype:
        range_ = property_.datatype.label
    elif property_.range:
        range_ = property_.range.label

    linkml_attr = LinkMLAttribute(
        slot_uri=_map_to_curie(property_.iri, prefixes),
        range=range_,
        multivalued=True if property_.multiplicity[1] > 1 else False,
        required=True if property_.multiplicity[0] > 0 else False,
        description=property_.comment,
    )
    linkml_attr._name = property_.label

    return linkml_attr


def _generate_class(class_: CIMRDFSClass, prefixes: dict[str, str], super_class: Optional[str] = None) -> LinkMLClass:
    linkml_class = LinkMLClass(
        class_uri=_map_to_curie(class_.iri, prefixes),
        attributes={attr.label: _generate_attribute(attr, prefixes) for attr in class_.attributes.values()} or None,
        is_a=super_class,
        description=class_.comment,
    )
    linkml_class._name = class_.label or class_.iri.split("#")[-1]

    return linkml_class


def _generate_enum(enum: CIMRDFSEnumeration, prefixes: dict[str, str]) -> LinkMLEnum:
    linkml_enum = LinkMLEnum(
        enum_uri=enum.iri,
        permissible_values={val.label: _generate_enum_value(val, prefixes) for val in enum.values.values()},
    )
    linkml_enum._name = enum.label or enum.iri.split("#")[-1]

    return linkml_enum


def _generate_enum_value(enum_val: CIMRDFSEnumValue, prefixes: dict[str, str]) -> LinkMLEnumValue:
    linkml_enum_val = LinkMLEnumValue(description=enum_val.comment, meaning=_map_to_curie(enum_val.iri, prefixes))
    linkml_enum_val._name = enum_val.label or enum_val.iri.split("#")[-1]

    return linkml_enum_val


def generate_schema(
    namespaces: dict[str, str],
    ontology_meta: CGMESOntologyDeclaration,
    profile_meta: CGMESProfileDeclaration,
    classes: dict[str, CIMRDFSClass],
    enums: dict[str, CIMRDFSEnumeration],
):
    prefixes = {"linkml": "https://w3id.org/linkml/", **{v: k for k, v in namespaces.items()}}
    schema = LinkMLSchema(
        id=profile_meta.iri,
        name=profile_meta.label or ontology_meta.keyword,
        description=ontology_meta.description,
        prefixes=prefixes,
        imports=["linkml:types"],
        default_curi_maps=["semweb_context"],
        default_range="string",
        default_prefix=None,
        classes={},
        slots={},
        enums={},
    )

    for class_iri, class_ in classes.items():
        try:
            super_class_label = classes[classes[class_iri].subclass_of].label
        except KeyError:
            super_class_label = None
        linkml_class = _generate_class(class_, prefixes, super_class_label)
        schema.classes[linkml_class._name] = linkml_class
    if not schema.classes:
        schema.classes = None

    for enum in enums.values():
        linkml_enum = _generate_enum(enum, prefixes)
        schema.enums[linkml_enum._name] = linkml_enum
    if not schema.enums:
        schema.enums = None

    if not schema.slots:
        schema.slots = None

    return schema
