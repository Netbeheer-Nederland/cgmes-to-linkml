from pathlib import Path
from typing import Optional

import yaml

from cgmes2linkml.cgmes.model import CIMRDFSClass, CIMRDFSProperty
from cgmes2linkml.linkml.model import LinkMLClass, LinkMLAttribute


def _map_datatype(value):
    return ""


def _generate_attribute(property_: CIMRDFSProperty) -> LinkMLAttribute:
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


def _generate_class(class_: CIMRDFSClass, super_class: Optional[str] = None) -> LinkMLClass:
    return LinkMLClass(
        _name=class_.label,
        class_uri=class_.iri,
        attributes={
            attr.label: _generate_attribute(attr) for attr in class_.attributes.values()
        },
        is_a=super_class,
        description=class_.comment,
    )


def generate_schema(classes: dict[str, CIMRDFSClass]):
    for class_iri, class_ in classes.items():
        super_class_label = classes[class_iri].label
        linkml_class = _generate_class(class_, super_class_label)

        # print(linkml_class.model_dump_json())
        print(yaml.safe_dump(linkml_class.model_dump(mode="json"), sort_keys=False))
        break
