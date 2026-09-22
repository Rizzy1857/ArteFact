# Troubleshooting

Start with `artefact health`.

- **Optional module unavailable:** install the named extra, such as `pip install -e ".[disk]"`.
- **ExifTool not found:** install the OS package and confirm `exiftool` is on `PATH`.
- **Cannot inspect a disk filesystem:** install `pytsk3`; confirm the image format and partition number.
- **E01/AFF conversion unavailable:** install the relevant external image library/tool, or convert to raw format first.
- **Volatility returns no results:** confirm the dump format, symbols, and Volatility version. Basic strings and IOC extraction remain available.
- **Qt GUI unavailable:** install the `gui` extra; headless systems should use the CLI.
- **Plugin rejected:** compare the archive and entrypoint hashes, API version, dependency list, and HTTPS URLs.
- **Permission error:** work in a writable output directory. Elevate only for an operation that explicitly requires mounting or live-system access.
- **Large evidence:** use streaming commands and `hash --cache`; avoid placing output inside an input directory being recursively processed.

Run `python -m pytest --run-system --performance` when validating a development checkout.
