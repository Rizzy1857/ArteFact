# 📘 Usage Guide

This guide walks you through ArteFact’s key modules. Whether you're investigating a compromised system or just exploring cyber forensics, you're in the right place.

---

## 1️⃣ File Carving

Recover files from raw storage dumps.

```bash
python src/carving/file_carver.py -i test_files/sample.img -o output/
```
### Options:

`-i`: Input disk/image file

`-o`: Output directory to store carved files

`--types`: (optional) File types to look for (`jpg`, `pdf`, etc.)

## 2️⃣ Memory Analysis

Parse raw memory dumps for strings, process lists, and indicators.

```bash
python src/memory/mem_parser.py -d test_dumps/dump1.raw
```
### Options (Again):

`-d`: Memory dump file

`--strings`: Extract printable strings

`--pslist`: Attempt process list reconstruction

Future update will support integration with Volatility plugins(*hopefully*).

## 3️⃣ Metadata Extraction

Pull metadata from images, documents, and media files.

```bash
python src/metadata/meta_extractor.py -f sample.jpg
```
`-f`: File to extract metadata from.

`--deep`: Use `exiftool` for deeper extraction (if installed).

## 5️⃣ Hash Checker

Generate and compare file hashes.

```bash
python src/hash_tools/hash_checker.py -f suspect_file.txt -a sha256
```
### Options:

`-f`: File to hash

`-a`: Hash algorithm (`md5`, `sha1`, `sha256`)

`--compare`: Provide a hash string to compare

## More Help

Each module supports --help:

example:

```bash
python src/carving/file_carver.py --help
```