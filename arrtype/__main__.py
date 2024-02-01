from pathlib import Path

import click
from memobj import WindowsProcess

import arrtype


@click.command()
@click.argument(
    "outfile",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    default="use revision"
)
@click.option("--version", type=int, default=2, show_default=True)
@click.option("--indent", type=int, default=None)
def main(outfile: Path, version: int, indent: int | None):
    match version:
        case 1:
            dump_type = arrtype.JsonTypeDumperV1
        case 2:
            dump_type = arrtype.JsonTypeDumperV2
        case _:
            click.echo(f"{version} is not a supported version")
            exit(1)

    process = WindowsProcess.from_name("Pirate.exe")
    wiz_bin = process.executable_path.parent
    revision_file = wiz_bin / "revision.dat"

    if not revision_file.exists():
        raise FileNotFoundError(f"revision.dat not found in {wiz_bin}")

    revision = revision_file.read_text().strip()

    if str(outfile) == "use revision" or outfile == b"use revision":
        outfile = Path(revision.replace(".", "_") + ".json")

    click.echo(f"dumping types for revision {revision} to {outfile}")

    tree = arrtype.get_type_tree()
    dumper = dump_type(tree)

    dumper.dump(outfile, indent=indent)


if __name__ == "__main__":
    main()
