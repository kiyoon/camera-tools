import typer

from .bulk_image_resize import bulk_image_resize
from .datename import datename
from .fast_image_resize import fast_image_resize
from .jpgs_to_gif import jpgs_to_gif
from .organise_images_like_dir import organise_images_like_dir

app = typer.Typer(no_args_is_help=True)


app.command(no_args_is_help=True)(datename)
app.command(no_args_is_help=True)(bulk_image_resize)
app.command(no_args_is_help=True)(fast_image_resize)
app.command(no_args_is_help=True)(jpgs_to_gif)
app.command(no_args_is_help=True)(organise_images_like_dir)


def main():
    app()
