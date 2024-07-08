import typer

from .bulk_image_resize import bulk_image_resize
from .datename import datename
from .jpgs_to_gif import jpgs_to_gif

app = typer.Typer(no_args_is_help=True)


app.command()(datename)
app.command()(bulk_image_resize)
app.command()(jpgs_to_gif)


def main():
    app()
