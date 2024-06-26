# File-by-file API

The file-by-file API allows the user to search the license of file providing:

- a checksum; or:
- a package, version, path

## URL schema

- /copyright/api/sha256/?checksum=

  - Optional parameter package name: &package=
  - Optional parameter suite (suite alias or latest): &suite=

- /copyright/api/file/PACKAGE/VERSION/PATH/
  - Version can be a suite alias (jessie), a package version or the keywords all and
    latest
  - Package is not optional. Otherwise finding the file would consume a lot of time.
    Possible workaround #761108

## JSON structure

API should be homogeneous, meaning that the result provided in case of a checksum or a
(path, package, version) should have the same structure. This is interesting for the end
user as s.he will have to parse only one type of results.

Emitting license (and copyright) statements is the responsibility of external "license
oracles". Debsources only makes those statements available via this API. Several license
oracles are supported; the main one is "debian", which gives access to the license
information available in `debian/copyright` files. Other license oracles will be
supported in the future (see relevant section below). The API will label each license
statement with the name of the emitting oracle.

It is also possible that a search by checksum returns more than one result since the
exact same file might appear in different packages, or different versions of the same
package. It is possible that the license statements associated to the different
occurrences of a given file will differ from one another. These inconsistencies will not
be hidden by the API, but rather returned with information about its context.

To address these requirements the JSON structure should have the following form:

```json
{
  "results": [
    {
      "sha256": "----",
      "copyright": [
        {
          "path": "----",
          "package": "pkg2",
          "version": "v2",
          "license": "GPL2",
          "origin": "----",
          "oracle": "debian"
        },
        {
          "path": "----",
          "package": "pkg2",
          "version": "v3",
          "license": "GPL3",
          "origin": "----",
          "oracle": "debian"
        }
      ]
    },
    {
      "sha256": "----",
      "copyright": [
        {
          "path": "----",
          "package": "pkg1",
          "version": "v1",
          "license": "GPL3",
          "origin": "----",
          "oracle": "debian"
        },
        {
          "path": "----",
          "package": "pkg1",
          "version": "v1",
          "license": "GPL2",
          "origin": "----",
          "oracle": "ninka"
        }
      ]
    }
  ]
}
```

The copyright dictionary contains a list with all the appearances of the specific
checksum, providing their package, version, path info along with the license synopsis,
its origin (e.g., link to the `debian/copyright` file) and the license oracle used to
retrieve the license.

In case the user searches using a file name, package, version then the copyright list
will contain a single result for each license oracle used.

The results field allows grouping by checksum. This is necessary for searching with file
name / package with 'all' as version since each file might have different checksums
because of the changes between the versions.

# Batch API

This API allows the user to search the license of many files (batch) at once providing
their checksum

## URL schema

- /copyright/api/sha256/

The API accepts an HTTP POST request. The data must be form-encoded, repeating the
checksum parameter for multiple values. For example, if you are using python requests to
create the POST request then the dictionnary containing the values should have the
following structure:

```json
{
    "checksums": [SUM1, SUM2, SUM3, ...],
    "package": PACKAGE,
    "suite": SUITE
}
```

Checksums is a list of sha256 checksums. The package and suite parameters are optional.
Suite can be a suite alias or latest.

## JSON structure

The results are homogeneous, independently on whether the file-by-file API or the batch
one has been invoked.

```json
{
    result: [
        {
            sha256: checksum1,
            copyright: [
                {
                    path: "----",
                    package: "pkg2",
                    version: "v2",
                    license: "GPL2",
                    origin: "----",
                    oracle: "debian",
                },
                {
                    path: "----",
                    package: "pkg2",
                    version: "v3",
                    license: "GPL3",
                    origin: "----",
                    oracle: "debian"
                },
            ]
        },
        {
            sha256: checksum2,
            copyright: [
                {
                    path: "----",
                    package: "pkg",
                    version: "v2",
                    license: "BSD",
                    origin: "----",
                    oracle: "debian",
                },
                {
                    path: "----",
                    package: "pkg2",
                    version: "v3",
                    license: "GPL3",
                    origin: "----",
                    oracle: "debian"
                },
            ]
        },
    ]
}
```

The JSON structure is identical to the file-by-file one with the results field
containing the list of checksums provided by the user along with the relevant copyright
dictionnary.

# Supported license oracles

- **debian**: corresponding to information retrieved from `debian/copyright` files.

  If `debian/copyright` is [machine-readable][1] for the requested file, the license
  field returned by this API will contain the value of the relevant "License:" field in
  `debian/copyright`

  If `debian/copyright` is not machine-readable, the license field will be null.

[1]: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/

Other license oracles might be added in the future. In particular we are considering
adding support for FOSSology and Ninka. The API is extensible enough to provide the user
with the those results using the oracle field. Thus the available information mined by
the oracles will be added using another dictionary field, specific to the oracle in
question, in the copyright field.

# Filters

The URL schemes could be extended with other optional parameters such as:

- &oracle= return only license statements emitted by the requested license oracle
