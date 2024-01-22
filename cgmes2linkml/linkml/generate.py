from pathlib import Path
from typing import Optional

from cgmes2linkml.cgmes.model import (
    CIMRDFSClass,
    CIMRDFSProperty,
    CGMESOntologyDeclaration,
    CGMESProfileDeclaration,
    CIMRDFSEnumeration,
    CIMRDFSEnumValue,
)
from cgmes2linkml.linkml.model import LinkMLClass, LinkMLAttribute, LinkMLSchema, LinkMLEnum, LinkMLEnumValue


def _map_primitive_datatype(value):
    match value:
        case "#Float":
            return "float"
        case "#Integer":
            return "integer"
        case "#DateTime":
            return "date"
        case "#String":
            return "string"
        case "#Boolean":
            return "boolean"
        case "#Decimal":
            return "double"  # Is this right?
        case "#MonthDay":
            return "date"  # Is this right?
        case "#Date":
            return "date"
        case _:
            return "string"  # TODO.


def _generate_attribute(property_: CIMRDFSProperty) -> LinkMLAttribute:
    if property_.datatype:
        range_ = _map_primitive_datatype(property_.datatype)
    else:
        range_ = property_.range.label

    linkml_attr = LinkMLAttribute(
        slot_uri=property_.iri,
        range=range_,
        multivalued=True if property_.multiplicity[1] > 1 else False,
        required=True if property_.multiplicity[0] > 0 else False,
        description=property_.comment,
    )
    linkml_attr._name = property_.label

    return linkml_attr


def _generate_class(class_: CIMRDFSClass, super_class: Optional[str] = None) -> LinkMLClass:
    linkml_class = LinkMLClass(
        class_uri=class_.iri,
        attributes={attr.label: _generate_attribute(attr) for attr in class_.attributes.values()},
        is_a=super_class,
        description=class_.comment,
    )
    linkml_class._name = class_.label or class_.iri.split("#")[-1]

    return linkml_class


def _generate_enum(enum: CIMRDFSEnumeration) -> LinkMLEnum:
    linkml_enum = LinkMLEnum(
        enum_uri=enum.iri,
        permissible_values={val.label: _generate_enum_value(val) for val in enum.values.values()},
    )
    linkml_enum._name = enum.label or enum.iri.split("#")[-1]

    return linkml_enum


def _generate_enum_value(enum_val: CIMRDFSEnumValue) -> LinkMLEnumValue:
    linkml_enum_val = LinkMLEnumValue(
        description=enum_val.comment,
        meaning=enum_val.iri
    )
    linkml_enum_val._name = enum_val.label or enum_val.iri.split("#")[-1]

    return linkml_enum_val


def generate_schema(
    namespaces: dict[str, str],
    ontology_meta: CGMESOntologyDeclaration,
    profile_meta: CGMESProfileDeclaration,
    classes: dict[str, CIMRDFSClass],
    enums: dict[str, CIMRDFSEnumeration],
):
    schema = LinkMLSchema(
        id=profile_meta.iri,
        name=profile_meta.label or ontology_meta.keyword,
        description=ontology_meta.description,
        prefixes={"linkml": "https://w3id.org/linkml/", **{v: k for k, v in namespaces.items()}},
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
        linkml_class = _generate_class(class_, super_class_label)
        schema.classes[linkml_class._name] = linkml_class

    for enum in enums.values():
        linkml_enum = _generate_enum(enum)
        schema.enums[linkml_enum._name] = linkml_enum

    return schema
