"""Command-line interface for ArteFact."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, List, Optional

from Artefact import __codename__, __version__


TOOLS = {
    "hash": "Hash files and directories",
    "carve": "Recover files from raw images",
    "meta": "Extract file metadata",
    "timeline": "Generate filesystem timelines",
    "memory": "Analyze memory dumps",
    "mount": "Inspect and extract disk images",
    "liveops": "Collect live system information",
    "network": "Analyze PCAP network captures",
    "case": "Create and update forensic cases",
    "report": "Generate forensic case reports",
    "plugins": "Inspect verified analysis plugins",
    "health": "Check runtime dependencies and capabilities",
    "gui": "Launch the optional Qt desktop interface",
    "disk": "Perform advanced disk and registry analysis",
}

COMMAND_GROUPS = {
    "Evidence analysis": ("hash", "carve", "meta", "timeline", "memory", "network"),
    "Disk and live systems": ("mount", "disk", "liveops"),
    "Case workflow": ("case", "report", "gui"),
    "Extensibility and diagnostics": ("plugins", "health"),
}


class ArtefactHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Readable help that preserves examples and displays useful defaults."""

    def __init__(self, prog: str):
        super().__init__(prog, max_help_position=30, width=100)

    def _get_help_string(self, action: argparse.Action) -> str:
        help_text = action.help or ""
        useful_default = not (
            action.default is None
            or action.default is False
            or action.default == ""
            or action.default == argparse.SUPPRESS
        )
        if useful_default and "%(default)" not in help_text and action.option_strings:
            help_text += " (default: %(default)s)"
        return help_text


def _examples(*lines: str) -> str:
    return "Examples:\n  " + "\n  ".join(lines)


def _json(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    category_lines = [f"  {heading}:\n    {', '.join(commands)}"
                      for heading, commands in COMMAND_GROUPS.items()]
    parser = argparse.ArgumentParser(
        prog="artefact",
        description=("ArteFact - case-oriented digital forensics\n\n"
                     "Inspect evidence, preserve provenance, and produce reproducible reports."),
        epilog=("Command groups:\n" + "\n".join(category_lines) +
                "\n\nGetting started:\n"
                "  artefact health\n"
                "  artefact help hash\n"
                "  artefact case case.json --create \"Incident review\""),
        formatter_class=ArtefactHelpFormatter,
    )
    global_options = parser.add_argument_group("global options")
    global_options.add_argument("-V", "--version", action="store_true", help="show version and codename")
    global_options.add_argument("--list-tools", action="store_true", help="list commands in category order")
    global_options.add_argument("-I", "--interactive", action="store_true", help="launch the interactive command prompt")
    sub = parser.add_subparsers(dest="command", title="commands", metavar="COMMAND",
                                description="Run 'artefact help COMMAND' for detailed examples.")

    def command(name: str, *examples: str, aliases=None) -> argparse.ArgumentParser:
        child = sub.add_parser(
            name, aliases=aliases or [], help=TOOLS[name], description=TOOLS[name] + ".",
            epilog=_examples(*examples) if examples else None,
            formatter_class=ArtefactHelpFormatter,
        )
        child.set_defaults(command=name)
        return child

    help_parser = sub.add_parser(
        "help", help="Show detailed help for a command", description="Show command-specific help.",
        formatter_class=ArtefactHelpFormatter,
    )
    help_parser.add_argument("topic", nargs="?", choices=list(TOOLS), metavar="COMMAND",
                             help="command to explain; omit for the main help page")

    hash_parser = command("hash", "artefact hash evidence.bin",
                          "artefact hash evidence/ --algorithm sha512 --no-recursive",
                          "artefact hash disk.img --cache .hash-cache.json")
    hash_parser.add_argument("path", type=Path, metavar="PATH", help="file or directory to hash")
    hash_parser.add_argument("-a", "--algorithm", choices=["md5", "sha1", "sha256", "sha512"],
                             default="sha256", help="digest algorithm")
    hash_parser.add_argument("--recursive", dest="recursive", action="store_true", default=True,
                             help="include nested directories")
    hash_parser.add_argument("--no-recursive", dest="recursive", action="store_false",
                             help="hash only files directly inside PATH")
    hash_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    hash_parser.add_argument("--cache", type=Path, metavar="FILE",
                             help="reuse unchanged hashes from a persistent cache")

    carve_parser = command("carve", "artefact carve -i disk.img -o recovered --types jpg pdf")
    carve_parser.add_argument("-i", "--input", required=True, type=Path, metavar="IMAGE",
                              help="raw disk or memory image")
    carve_parser.add_argument("-o", "--output", required=True, type=Path, metavar="DIR",
                              help="directory for recovered files")
    carve_parser.add_argument("--types", nargs="+", help="file types (space- or comma-separated)")

    meta_parser = command("meta", "artefact meta -f photograph.jpg --deep", aliases=["metadata"])
    meta_parser.add_argument("-f", "--file", required=True, type=Path, metavar="FILE",
                             help="file to inspect")
    meta_parser.add_argument("--deep", action="store_true", help="also query ExifTool when available")
    meta_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    timeline_parser = command("timeline", "artefact timeline evidence/ --format json",
                              "artefact timeline evidence.bin --format markdown")
    timeline_parser.add_argument("path", type=Path, metavar="PATH", help="file or directory to inspect")
    timeline_parser.add_argument("-f", "--format", choices=["json", "markdown", "csv"],
                                 default="markdown", help="output serialization")
    timeline_parser.add_argument("--no-recursive", action="store_true",
                                 help="do not scan nested directories")

    memory_parser = command("memory", "artefact memory -i memory.raw --strings --iocs",
                            "artefact memory -i memory.raw --carve -o recovered --types pe elf")
    memory_parser.add_argument("-i", "--input", required=True, type=Path, metavar="DUMP",
                               help="memory dump to analyze")
    memory_parser.add_argument("-o", "--output", type=Path, metavar="DIR",
                               help="destination required by --carve")
    memory_parser.add_argument("--strings", action="store_true", help="extract printable strings")
    memory_parser.add_argument("--iocs", action="store_true", help="extract indicators from strings")
    memory_parser.add_argument("--carve", action="store_true", help="recover PE and ELF binaries")
    memory_parser.add_argument("--types", nargs="+", metavar="TYPE", help="binary types to recover")
    memory_parser.add_argument("--min-length", type=int, default=4, metavar="N",
                               help="minimum extracted string length")
    memory_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    mount_parser = command("mount", "artefact mount -i disk.img --list",
                           "artefact mount -i disk.img --extract 0 -o extracted")
    mount_parser.add_argument("-i", "--input", required=True, type=Path, metavar="IMAGE",
                              help="disk image to inspect")
    mount_parser.add_argument("--list", action="store_true", dest="list_partitions",
                              help="list partitions (default action)")
    mount_parser.add_argument("--extract", type=int, metavar="PARTITION",
                              help="extract the selected partition")
    mount_parser.add_argument("-o", "--output", type=Path, metavar="DIR",
                              help="destination required by --extract")

    live_parser = command("liveops", "artefact liveops --collect processes network")
    live_parser.add_argument("--collect", nargs="+", choices=["processes", "network"], required=True,
                             metavar="ARTIFACT", help="one or more live artifact classes")
    live_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    network_parser = command("network", "artefact network -i traffic.pcap -o network.json",
                             "artefact network -i traffic.pcap --extract-http objects --threat-feed feed.json",
                             aliases=["pcap"])
    network_parser.add_argument("-i", "--input", required=True, type=Path, metavar="PCAP",
                                help="classic Ethernet PCAP capture")
    network_parser.add_argument("-o", "--output", type=Path, metavar="JSON",
                                help="write analysis to a JSON file instead of stdout")
    network_parser.add_argument("--threat-feed", type=Path, metavar="JSON",
                                help="local IOC feed to correlate")
    network_parser.add_argument("--extract-http", type=Path, metavar="DIR",
                                help="recover complete HTTP response bodies")

    case_parser = command("case", "artefact case case.json --create \"Incident 42\" --id CASE-42",
                          "artefact case case.json --add-evidence disk.img --actor analyst")
    case_parser.add_argument("case_file", type=Path, metavar="CASE.json", help="case record to create or update")
    case_parser.add_argument("--create", metavar="TITLE", help="create a new case with this title")
    case_parser.add_argument("--id", dest="case_id", metavar="ID", help="case identifier used with --create")
    case_parser.add_argument("--add-evidence", type=Path, metavar="FILE", help="hash and attach evidence")
    case_parser.add_argument("--description", default="", metavar="TEXT", help="evidence description")
    case_parser.add_argument("--actor", default="analyst", metavar="NAME", help="chain-of-custody actor")

    report_parser = command("report", "artefact report case.json -o report.pdf --format pdf",
                            "artefact report case.json -o custom.html --template template.html")
    report_parser.add_argument("case_file", type=Path, metavar="CASE.json", help="case record to render")
    report_parser.add_argument("-o", "--output", required=True, type=Path, metavar="FILE",
                               help="report destination")
    report_parser.add_argument("-f", "--format", choices=["markdown", "html", "json", "pdf"],
                               default="markdown", help="report format")
    report_parser.add_argument("--template", type=Path, metavar="FILE", help="safe custom text template")

    plugin_parser = command("plugins", "artefact plugins --root plugins --verify",
                            "artefact plugins --install analyzer --index https://example.test/index.json")
    plugin_parser.add_argument("--root", type=Path, default=Path("plugins"), metavar="DIR",
                               help="local plugin registry")
    plugin_parser.add_argument("--verify", action="store_true", help="verify installed entrypoint hashes")
    plugin_parser.add_argument("--install", metavar="NAME", help="install a plugin from --index")
    plugin_parser.add_argument("--index", metavar="HTTPS_URL", help="trusted HTTPS marketplace index")

    command("health", "artefact health")
    gui_parser = command("gui", "artefact gui --case case.json")
    gui_parser.add_argument("--case", dest="case_file", type=Path, metavar="CASE.json",
                            help="open this case at startup")

    disk_parser = command("disk", "artefact disk --inventory -i disk.img --partition 0",
                          "artefact disk --recover-deleted -i disk.img -o recovered",
                          "artefact disk --registry -i NTUSER.DAT", "artefact disk --shadows")
    disk_actions = disk_parser.add_mutually_exclusive_group(required=True)
    disk_actions.add_argument("--inventory", action="store_true", help="list filesystem entries")
    disk_actions.add_argument("--recover-deleted", action="store_true", help="recover unallocated entries")
    disk_actions.add_argument("--registry", action="store_true", help="inspect an offline Registry hive")
    disk_actions.add_argument("--shadows", action="store_true", help="list Windows shadow copies")
    disk_parser.add_argument("-i", "--input", type=Path, metavar="PATH",
                             help="disk image, Registry hive, or volume for the selected action")
    disk_parser.add_argument("-p", "--partition", type=int, default=0, metavar="N",
                             help="partition address")
    disk_parser.add_argument("-o", "--output", type=Path, metavar="DIR",
                             help="recovery destination")
    disk_parser.add_argument("--pattern", metavar="GLOB", help="limit recovered filenames")
    return parser


def _normalize_types(values: Optional[List[str]]) -> Optional[List[str]]:
    if not values:
        return None
    return [item.lower() for value in values for item in value.split(",") if item]


def _command_parser(parser: argparse.ArgumentParser, command: str) -> argparse.ArgumentParser:
    """Resolve a command parser for the dedicated help command."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[command]
    raise KeyError(command)


def _run(args: argparse.Namespace) -> int:
    if args.version:
        print(f'ARTEFACT {__version__} "{__codename__}"')
        return 0
    if args.list_tools:
        print("ARTEFACT command groups:")
        for heading, commands in COMMAND_GROUPS.items():
            print(f"\n{heading}")
            for name in commands:
                print(f"  {name:<10} {TOOLS[name]}")
        return 0
    if args.interactive:
        from Artefact.console import interactive_mode
        return interactive_mode()
    if not args.command:
        build_parser().print_help()
        return 0
    if args.command == "help":
        parser = build_parser()
        (parser if args.topic is None else _command_parser(parser, args.topic)).print_help()
        return 0

    if args.command == "hash":
        from Artefact.modules.hasher import hash_directory, hash_file, hash_file_cached
        result = (hash_directory(args.path, args.algorithm, recursive=args.recursive)
                  if args.path.is_dir() else
                  hash_file_cached(args.path, args.algorithm, args.cache) if args.cache else
                  hash_file(args.path, args.algorithm))
        if isinstance(result, dict) or args.json:
            _json(result)
        else:
            print(f"{args.algorithm}: {result}  {args.path}")
    elif args.command == "carve":
        from Artefact.modules.carving import carve_files
        files = carve_files(args.input, args.output, types=_normalize_types(args.types))
        print(f"Carved {len(files)} file(s) to {args.output}")
    elif args.command == "meta":
        from Artefact.modules.metadata import extract_metadata
        _json(extract_metadata(args.file, deep=args.deep))
    elif args.command == "timeline":
        from Artefact.modules.timeline import (create_timeline_from_directory,
            extract_file_timestamps, timeline_to_csv, timeline_to_json, timeline_to_markdown)
        events = (create_timeline_from_directory(args.path, recursive=not args.no_recursive)
                  if args.path.is_dir() else extract_file_timestamps(str(args.path)))
        exporters = {"json": timeline_to_json, "markdown": timeline_to_markdown, "csv": timeline_to_csv}
        print(exporters[args.format](events))
    elif args.command == "memory":
        from Artefact.modules.memory import carve_binaries, extract_iocs, extract_strings
        if not (args.strings or args.iocs or args.carve):
            raise ValueError("choose at least one action: --strings, --iocs, or --carve")
        strings = extract_strings(args.input, min_length=args.min_length) if (args.strings or args.iocs) else {}
        result = {}
        if args.strings:
            result["strings"] = strings
        if args.iocs:
            flat = [text for matches in strings.values() for text, _ in matches]
            result["iocs"] = extract_iocs(flat)
        if args.carve:
            if not args.output:
                raise ValueError("--output is required with --carve")
            result["carved"] = carve_binaries(args.input, args.output, types=_normalize_types(args.types))
        _json(result)
    elif args.command == "mount":
        from Artefact.modules.mount import extract_partition, list_partitions
        if args.extract is not None:
            if not args.output:
                raise ValueError("--output is required with --extract")
            extract_partition(args.input, args.extract, args.output)
        else:
            list_partitions(args.input)
    elif args.command == "liveops":
        from Artefact.modules.liveops import collect
        _json(collect(args.collect))
    elif args.command == "network":
        from Artefact.modules.network import analyze_pcap, extract_http_objects, parse_pcap
        result = analyze_pcap(args.input, args.threat_feed)
        if args.extract_http:
            result["extracted_http"] = [str(path) for path in
                                        extract_http_objects(parse_pcap(args.input), args.extract_http)]
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            print(f"Network report written to {args.output}")
        else:
            _json(result)
    elif args.command == "case":
        from Artefact.case import Case
        if args.create:
            case = Case.create(args.create, args.case_id)
        elif args.case_file.is_file():
            case = Case.load(args.case_file)
        else:
            raise FileNotFoundError(args.case_file)
        if args.add_evidence:
            case.add_evidence(args.add_evidence, args.description, args.actor)
        case.save(args.case_file)
        _json({"case_id": case.id, "path": str(args.case_file), "evidence_count": len(case.evidence)})
    elif args.command == "report":
        from Artefact.case import Case
        from Artefact.reporting import ReportBuilder
        path = ReportBuilder(Case.load(args.case_file)).write(args.output, args.format, args.template)
        print(f"Report written to {path}")
    elif args.command == "plugins":
        from Artefact.plugins import PluginMarketplace, PluginRegistry
        registry = PluginRegistry(args.root)
        if args.install:
            if not args.index:
                raise ValueError("--index is required with --install")
            installed = PluginMarketplace(registry).install(args.index, args.install)
            _json({"installed": installed.name, "version": installed.version})
            return 0
        if args.index:
            raise ValueError("--index is only used together with --install NAME")
        items = registry.discover()
        _json([{"name": item.name, "version": item.version,
                "verified": registry.verify(item) if args.verify else None}
               for item in items])
    elif args.command == "health":
        from Artefact.health import dependency_health
        result = dependency_health()
        _json(result)
        return 0 if result["healthy"] else 1
    elif args.command == "gui":
        from Artefact.gui import launch_gui
        return launch_gui(args.case_file)
    elif args.command == "disk":
        from Artefact.modules.disk_forensics import (analyze_registry_hive,
            filesystem_inventory, list_volume_shadows, recover_deleted_files)
        if args.shadows:
            _json(list_volume_shadows(str(args.input) if args.input else None))
        elif args.registry:
            if not args.input:
                raise ValueError("--input is required for registry analysis")
            _json(analyze_registry_hive(args.input))
        elif args.inventory:
            if not args.input:
                raise ValueError("--input is required for filesystem inventory")
            _json(filesystem_inventory(args.input, args.partition))
        else:
            if not args.input or not args.output:
                raise ValueError("--input and --output are required for deleted-file recovery")
            _json([str(path) for path in recover_deleted_files(
                args.input, args.partition, args.output, args.pattern)])
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        return _run(parser.parse_args(argv))
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        print(f"artefact: error: {exc}", file=sys.stderr)
        command = argv[0] if argv and argv[0] in TOOLS else None
        print(f"Try 'artefact help {command}' for examples." if command else
              "Try 'artefact --help' for command guidance.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nartefact: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
