from pathlib import Path

import click
import yaml

from cimrdfs2linkml.cimrdfs.parse import parse_profile
from cimrdfs2linkml.linkml.generate import generate_schema


@click.command()
@click.argument("profile", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", default=Path("out.yaml"), type=click.Path(path_type=Path), help="Output LinkML schema file path.")
def cli(profile, output):
    namespaces, ontology_meta, profile_meta, classes, enums = parse_profile(profile)
    linkml_schema = generate_schema(namespaces, ontology_meta, profile_meta, classes, enums)
    # pprint(linkml_schema)

    with open(output, mode="w") as f:
        f.write(
            yaml.safe_dump(
                linkml_schema.model_dump(mode="json", exclude_unset=True, exclude_none=True),
                sort_keys=False,
            )
        )
    

if __name__ == "__main__":
    cli.main()
