from pathlib import Path
from pprint import pprint

from cgmes2linkml.cgmes.parse import parse_profile
from cgmes2linkml.linkml.generate import generate_schema

if __name__ == "__main__":
    tests_dir = Path("tests")
    eq_prof_fp = tests_dir / "data" / "IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf"
    classes, enums = parse_profile(eq_prof_fp)
    generate_schema(classes)
