import typer

from copilot_proxy import __version__
from copilot_proxy.server import run

cli = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


def version_callback(version: bool) -> None:
    if version:
        typer.echo(f"{__version__}")
        raise typer.Exit()


@cli.callback()
def version_option(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", help="Show version and exit", callback=version_callback
    ),
) -> None:
    pass


@cli.command(name="start")
def start(
    port: int = typer.Option(
        15432,
        "--port",
        "-p",
        help="The port number where the proxy server listens for incoming connections",
    )
) -> None:
    run(port)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
