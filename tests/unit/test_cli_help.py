from Artefact.cli import build_parser, main


def test_top_level_help_is_task_oriented():
    help_text = build_parser().format_help()
    assert "ArteFact - case-oriented digital forensics" in help_text
    assert "Command groups:" in help_text
    assert "Evidence analysis:" in help_text
    assert "artefact help hash" in help_text
    assert "commands:" in help_text


def test_dedicated_help_command_shows_descriptions_and_examples(capsys):
    assert main(["help", "network"]) == 0
    output = capsys.readouterr().out
    assert "classic Ethernet PCAP capture" in output
    assert "recover complete HTTP response bodies" in output
    assert "Examples:" in output
    assert "--threat-feed JSON" in output


def test_subcommand_aliases_resolve_to_canonical_command():
    parser = build_parser()
    assert parser.parse_args(["metadata", "-f", "sample.jpg"]).command == "meta"
    assert parser.parse_args(["pcap", "-i", "sample.pcap"]).command == "network"


def test_help_displays_defaults_where_useful():
    parser = build_parser()
    disk_help = next(action for action in parser._actions
                     if action.__class__.__name__ == "_SubParsersAction").choices["disk"].format_help()
    assert "partition address (default: 0)" in disk_help
    assert "--recover-deleted" in disk_help


def test_actionable_runtime_error_points_to_command_help(tmp_path, capsys):
    assert main(["memory", "-i", str(tmp_path / "memory.raw")]) == 1
    error = capsys.readouterr().err
    assert "choose at least one action" in error
    assert "artefact help memory" in error
