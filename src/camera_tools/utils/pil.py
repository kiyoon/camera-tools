from PIL import Image


def resample_str_to_pil_code(resample_str: str):
    resample_str = resample_str.lower()
    if resample_str == "nearest":
        return Image.Resampling.NEAREST
    elif resample_str == "bilinear":
        return Image.Resampling.BILINEAR
    elif resample_str == "bicubic":
        return Image.Resampling.BICUBIC
    elif resample_str == "lanczos":
        return Image.Resampling.LANCZOS

    raise NotImplementedError(
        f"'{resample_str}' not a recognised resampling algorithm."
    )
