from PIL import Image, ImageChops, ImageDraw, ImageFilter


def write_centre(draw, y, text, font, fill, img_width):
    """ Draws centre-aligned text.
    """
    text_width = font.getsize(text)[0]
    draw.text(((img_width-text_width)/2,y), text, font=font, fill=fill)


def write_with_outline(draw, xy, text, font, fill_text=(255,255,255,255), fill_outline=(0,0,0,255)):
    """ Draws text with a border
    """
    x, y = xy
    text_width = font.getsize(text)[0]

    # draw border
    draw.multiline_text((x-1, y-1), text, font=font, fill=fill_outline)
    draw.multiline_text((x+1, y-1), text, font=font, fill=fill_outline)
    draw.multiline_text((x-1, y+1), text, font=font, fill=fill_outline)
    draw.multiline_text((x+1, y+1), text, font=font, fill=fill_outline)

    # draw text
    draw.multiline_text(xy, text, font=font, fill=fill_text)#}}}


# https://stackoverflow.com/questions/12008493/create-a-halo-around-text-in-python-using-pil/12010040
def write_with_shadow(img, xy, text, font, fill=(255,255,255,255), halo_fill=(0,0,0,255)):
    x, y = xy
    halo = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).multiline_text((x+1, y+1), text, font = font, fill = halo_fill)
    blurred_halo = halo.filter(ImageFilter.GaussianBlur(radius=2))
    ImageDraw.Draw(blurred_halo).multiline_text(xy, text, font = font, fill = fill)
    return Image.composite(img, blurred_halo, ImageChops.invert(blurred_halo))

