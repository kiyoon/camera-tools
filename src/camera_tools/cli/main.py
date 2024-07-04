import typer

from .datename import datename

app = typer.Typer()


app.command()(datename)


def main():
    app()
