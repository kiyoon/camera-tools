import math
from pathlib import Path

from PIL import Image, ImageFont

from .pil_text import write_with_shadow

SCRIPT_DIR = Path(__file__).parent


def pillow_font_getsize(font: ImageFont.FreeTypeFont, text: str):
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


def _get_youtube_x(insta_x, fa_youtube_width, fa_insta_width):
    """Get YouTube icon's x position given Instagram x for centre-alignment."""
    return insta_x - (fa_youtube_width - fa_insta_width) // 2


def _get_youtube_y(insta_y, fa_insta_height, font_size):
    """Get YouTube icon's y position given Instagram y for centre-alignment."""
    return insta_y + fa_insta_height + font_size // 10


def _get_text_x(youtube_x, fa_youtube_width, font_size):
    return youtube_x + fa_youtube_width + font_size // 5


def _get_insta_xy_bottom_right(
    img_size,
    fa_youtube_size,
    fa_insta_size,
    youtube_name_size,
    insta_id_size,
    font_size,
):
    # get width and height of icon + text (signature)
    let_insta_x = 100  # example
    let_insta_y = 100
    let_youtube_x = _get_youtube_x(let_insta_x, fa_youtube_size[0], fa_insta_size[0])
    let_youtube_y = _get_youtube_y(let_insta_y, fa_insta_size[1], font_size)
    text_x = _get_text_x(let_youtube_x, fa_youtube_size[0], font_size)

    signature_height = let_youtube_y + fa_youtube_size[1] - let_insta_y
    signature_width = (
        text_x
        + max(youtube_name_size[0], insta_id_size[0])
        - min(let_youtube_x, let_insta_x)
    )

    # get insta xy
    insta_x_right = img_size[0] - signature_width - font_size // 2
    insta_y_bottom = img_size[1] - signature_height - font_size // 2

    return insta_x_right, insta_y_bottom


def watermark_signature(
    img: Image.Image, insta_id="kiyoon0", youtube_name="Kiyoon Kim"
):
    font_size = round(math.sqrt(img.width * img.height) / 50)
    font_logos = ImageFont.truetype(
        SCRIPT_DIR.parent / "fonts" / "FontAwesome.otf", font_size
    )
    font_name = ImageFont.truetype(
        SCRIPT_DIR.parent / "fonts" / "bureau agency fb.otf", font_size
    )

    fa_youtube = "\uf16a"
    fa_insta = "\uf16d"
    # fa_youtube_size = font_logos.getsize(fa_youtube)
    # fa_insta_size = font_logos.getsize(fa_insta)
    #
    # insta_id_size = font_name.getsize(insta_id)
    # youtube_name_size = font_name.getsize(youtube_name)

    fa_youtube_size = pillow_font_getsize(font_logos, fa_youtube)
    fa_insta_size = pillow_font_getsize(font_logos, fa_insta)

    insta_id_size = pillow_font_getsize(font_name, insta_id)
    youtube_name_size = pillow_font_getsize(font_name, youtube_name)

    insta_x, insta_y = _get_insta_xy_bottom_right(
        img.size,
        fa_youtube_size,
        fa_insta_size,
        youtube_name_size,
        insta_id_size,
        font_size,
    )
    youtube_x = _get_youtube_x(insta_x, fa_youtube_size[0], fa_insta_size[0])
    youtube_y = _get_youtube_y(insta_y, fa_insta_size[1], font_size)

    text_x = _get_text_x(youtube_x, fa_youtube_size[0], font_size)

    img = write_with_shadow(img, (insta_x, insta_y), fa_insta, font=font_logos)
    img = write_with_shadow(img, (youtube_x, youtube_y), fa_youtube, font=font_logos)

    img = write_with_shadow(img, (text_x, insta_y), insta_id, font=font_name)
    img = write_with_shadow(img, (text_x, youtube_y), youtube_name, font=font_name)

    return img


if __name__ == "__main__":
    pil_cover = Image.open("res/cover.png")
    pil_cover = watermark_signature(pil_cover)

    pil_cover.convert("RGB").save("0.jpg", quality=100)
    pil_cover.close()
