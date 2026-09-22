# Plugin development and marketplace format

Plugin API version: `2.0`.

Each plugin archive contains one top-level directory with `plugin.json` and its Python entrypoint:

```json
{
  "name": "example-analyzer",
  "version": "1.0.0",
  "entrypoint": "plugin.py",
  "api_version": "2.0",
  "sha256": "SHA256_OF_PLUGIN_PY",
  "description": "Example analyzer",
  "requires": ["some-distribution>=1"]
}
```

An HTTPS marketplace index has this shape:

```json
{
  "plugins": [
    {"name": "example-analyzer", "url": "https://example.test/example.zip", "sha256": "SHA256_OF_ZIP"}
  ]
}
```

Installation verifies the ZIP hash and safe paths, then verifies the entrypoint hash. Loading checks the API version and declared Python distributions. Plugin modules execute in the ArteFact process with the user’s permissions; verification does not sandbox behavior. Review source and trust the publisher before installation.
