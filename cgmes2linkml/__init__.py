"""
Transformation of a CGMES IEC-61970-501 Profile to a LinkML schema.

Rules:
    - RDFS class
        - no stereotype -> LinkML class
        - stereotype: #enumeration -> LinkML enum
        - stereotype: #Primitive -> ?
    - RDFS property -> LinkML class attribute (all properties are tightly coupled to the domain anyways)
    - Individual
        - stereotype: enum -> permissible value of enumeration

WIP ^
"""

import json
from xml.etree import ElementTree
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from pprint import pprint


@dataclass
class RdfsResource:
    iri: str
    label: str


@dataclass
class RdfsClass(RdfsResource):
    subclass_of: Optional["RdfsClass"] = None
    stereotype: Optional[str] = None
    comment: Optional[str] = None
    belongsToCategory: Optional[str] = None


@dataclass
class RdfProperty(RdfsResource):
    domain: str
    multiplicity: str
    range: Optional[str] = None
    datatype: Optional[str] = None
    is_fixed: Optional[str] = None
    stereotype: Optional[str] = None


def parse_profile(xml_tree):
    root = xml_tree.getroot()

    classes = []
    properties = []
    for resource in root.findall("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"):
        if (type_el := resource.find("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type")) is not None:
            type_ = type_el.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]
        match type_:
            case "http://www.w3.org/2000/01/rdf-schema#Class":
                classes.append(parse_class(resource))
            case "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property":
                # properties.append(parse_property(resource))
                continue
            case _:
                continue

    return classes, properties


def _get_stereotype(resource):
    stereo = resource.find(".{http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#}stereotype")
    stereotype = None
    if stereo is not None:
        stereotype = stereo.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource") or stereo.text
    return stereotype


def parse_property(resource):
    ...


def parse_class(xml_class):
    iri = xml_class.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"]

    stereotype = _get_stereotype(xml_class)
    match stereotype:  # Only values occurring for classes
        case "CIMDatatype":
            for child in xml_class.iter():
                pprint(child.attrib.keys())  # This way I can reverse engineer what occurs
        case "European":
            pass
        case "Primitive":
            pass
        case "http://iec.ch/TC57/NonStandard/UML#concrete":
            pass
        case "http://iec.ch/TC57/NonStandard/UML#enumeration":
            pass
        case None:
            pass
        case _:
            pass

    subclass_of = None
    subcls = xml_class.find(".rdfs:subClassOf", prefix_map)
    if subcls is not None:
        subclass_of = subcls.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]

    lbl = xml_class.find(".rdfs:label", prefix_map)
    if lbl is not None:
        label = lbl.text

    cmt = xml_class.find(".rdfs:comment", prefix_map)
    if cmt is not None:
        comment = cmt.text

    return RdfsClass(iri=iri, subclass_of=subclass_of, label=label, comment=comment)


def get_cims_classes(root, prefix_map):
    clss = []
    for cls in root.findall(
        ".//rdf:type[@rdf:resource='http://www.w3.org/2000/01/rdf-schema#Class']/..",
        prefix_map,
    ):
        clss.append(parse_class(cls))

    return clss


def to_linkml_class(rdfs_class):
    print(rdfs_class.attrib)


if __name__ == "__main__":
    prefix_map = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "cims": "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    }
    tests_dir = Path("tests")

    tree = ElementTree.parse(tests_dir / "data" / "IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf")
    # root = tree.getroot()

    # cims_classes = get_cims_classes(root, prefix_map)
    # for vals in cims_classes:
    #    print(vals)
    #    #print(f"{iri}: {vals}")
    ##linkml_class = to_linkml_class(first_class)
    parse_profile(tree)
