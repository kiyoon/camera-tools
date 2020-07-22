from PIL import Image, ImageChops, ImageDraw, ImageFilter

methods = {
    2: Image.FLIP_LEFT_RIGHT,
    3: Image.ROTATE_180,
    4: Image.FLIP_TOP_BOTTOM,
    5: Image.TRANSPOSE,
    6: Image.ROTATE_270,
    7: Image.TRANSVERSE,
    8: Image.ROTATE_90,
}

methods_inverse = {
    2: Image.FLIP_LEFT_RIGHT,
    3: Image.ROTATE_180,
    4: Image.FLIP_TOP_BOTTOM,
    5: Image.TRANSPOSE,
    6: Image.ROTATE_90,
    7: Image.TRANSVERSE,
    8: Image.ROTATE_270,
}

def _exif_orientation_to_transpose_method(orientation):
    return methods.get(orientation)


def _exif_orientation_to_inverse_transpose_method(orientation):
    return methods_inverse.get(orientation)


def exif_transpose_delete_exif(image):
    """
    If an image has an EXIF Orientation tag, return a new image that is
    transposed accordingly. Otherwise, return the image.
    :param image: The image to transpose.
    :return: An image.
    """
    exif = image.getexif()
    orientation = exif.get(0x0112)
    method = _exif_orientation_to_transpose_method(orientation)
    if method is not None:
        transposed_image = image.transpose(method)
        inverse_method = _exif_orientation_to_inverse_transpose_method(orientation)
        return transposed_image, orientation, inverse_method
    return image, orientation, None
