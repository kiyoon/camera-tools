from cyclopts import App, Parameter

from .. import __version__
from .bulk_image_resize import bulk_image_resize
from .datename import datename
from .fast_image_resize import fast_image_resize
from .jpgs_to_gif import jpgs_to_gif
from .organise_images_like_dir import organise_images_like_dir

app = App(
    help_format="markdown",
    default_parameter=Parameter(
        consume_multiple=True,  # Allow list of arguments without repeating --option a --option b ..
        negative=False,  # Do not make --no-option as a boolean flag
    ),
    version=__version__,
)


app.command()(datename)
app.command()(bulk_image_resize)
app.command()(fast_image_resize)
app.command()(jpgs_to_gif)
app.command()(organise_images_like_dir)


def main():
    app()
