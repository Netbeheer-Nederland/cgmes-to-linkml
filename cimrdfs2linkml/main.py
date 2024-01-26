from pathlib import Path
from pprint import pprint

import yaml

from cimrdfs2linkml.cimrdfs.parse import parse_profile
from cimrdfs2linkml.linkml.generate import generate_schema

if __name__ == "__main__":
    root_dir = Path(".")
    eq_prof_fp = root_dir / "data" / "IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf"
    namespaces, ontology_meta, profile_meta, classes, enums = parse_profile(eq_prof_fp)
    linkml_schema = generate_schema(namespaces, ontology_meta, profile_meta, classes, enums)
    # pprint(linkml_schema)

    with open("out.yaml", mode="w") as f:
        f.write(
            yaml.safe_dump(
                linkml_schema.model_dump(mode="json", exclude_unset=True, exclude_none=True),
                sort_keys=False,
            )
        )
