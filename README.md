# cimrdfs2linkml
Generates a LinkML schema from a CIM RDF Schema (as per IEC 61970-501).

> [!NOTE]
> Currently only RDFS 2020 serializations of the CGMES 3.0.0 profiles are supported. This is because of assumptions about the profile metadata baked into the code.

## Installation and Running

Install the dependencies, preferably using `poetry`, and make sure the (virtual) environment you're can find the `cimrdfs2linkml` package (e.g. by extending `$PYTHONPATH`).

Then, to run the script, simply run:

```shell
$ python cimrdfs2linkml/main.py
```

This will read `data/IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf` and generate a LinkML schema from it, which is written to `out.yaml`.

## Mapping
The CIM RDF Schema distinguishes between several stereotypes of classes. The following are handled by `cimrdfs2linkml`:

* `Primitive`: mapped to LinkML primitive data types.
* `CIMDatatype`: mapped to LinkML classes.
* `Enumeration`: mapped to LinkML enums.
* remaining classes are mapped to LinkML classes.

> [!NOTE]
> CIM data types each consist of a unit symbol, unit mulitplier and value. For each such data type the symbol and multiplier are fixed (`cims:isFixed`) to some enum value. This fixed value is currently ignored.

Furthermore, each RDF property pertaining to some class is mapped to a LinkML attribute of that class.

> [!NOTE]
> As is made clear by the class name prefix in all property URIs, all properties are tightly coupled to classes. For that reason all properties are mapped to class attributes rather than top-level slots, i.e. no top-level slots are generated.

## Implementation Notes
For the quick development of this script the library `xmltodict` is used. This works since the IEC 61970-501 spec demands the use of an XML serialization of the schema, but proper RDF parsing (and querying) using something like `rdflib` has benefits and probably needs to be done in the future.