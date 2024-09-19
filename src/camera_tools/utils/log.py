import inspect
import logging
import os
from datetime import datetime, timezone
from os import PathLike
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from camera_tools import __version__

logger = logging.getLogger(__name__)

console = Console(
    theme=Theme(
        {
            "logging.level.success": "green",
            "logging.level.error": "bold red blink",
            "logging.level.critical": "red blink",
            "logging.level.warning": "yellow",
        }
    )
)


def setup_logging(
    console_level: int = logging.INFO,
    log_dir: str | PathLike | None = None,
    output_files: list[str] | None = None,
    file_levels: list[int] | None = None,
):
    """
    Setup logging with RichHandler and FileHandler.

    You should call this function at the beginning of your script.

    Args:
        console_level: Logging level for console. Defaults to INFO or env var MLPROJECT_LOG_LEVEL.
        log_dir: Directory to save log files. If None, do not save log files.
        output_files: List of output file paths, relative to log_dir. If None, use default.
        file_levels: List of logging levels for each output file. If None, use default.
    """
    if log_dir is None:
        assert output_files is None, "output_files must be None if log_dir is None"
        assert file_levels is None, "file_levels must be None if log_dir is None"

        output_files = []
        file_levels = []
    else:
        log_dir = Path(log_dir)

        if output_files is None:
            output_files = ["{date:%Y%m%d-%H%M%S}-{name}-{levelname}-{version}.log"]
        if file_levels is None:
            file_levels = [logging.INFO]

    assert len(output_files) == len(
        file_levels
    ), "output_files and file_levels must have the same length"

    # NOTE: Initialise with NOTSET level and null device, and add stream handler separately.
    # This way, the root logging level is NOTSET (log all), and we can customise each handler's behaviour.
    # If we set the level during the initialisation, it will affect to ALL streams,
    # so the file stream cannot be more verbose (lower level) than the console stream.
    logging.basicConfig(
        format="",
        level=logging.NOTSET,
        stream=open(os.devnull, "w"),  # noqa: SIM115
    )

    # If you want to suppress logs from other modules, set their level to WARNING or higher
    # logging.getLogger('some_package.utils').setLevel(logging.WARNING)

    console_handler = RichHandler(
        level=console_level,
        show_time=True,
        show_level=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        console=console,
    )
    console_format = logging.Formatter(
        fmt="%(name)s - %(message)s",
        datefmt="%m/%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)

    f_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s: %(lineno)4d - %(levelname)s - %(message)s",
        datefmt="%y/%m/%d %H:%M:%S",
    )

    function_caller_module = inspect.getmodule(inspect.stack()[1][0])
    if function_caller_module is None:
        name_or_path = "unknown"
    elif function_caller_module.__name__ == "__main__":
        if function_caller_module.__file__ is None:
            name_or_path = function_caller_module.__name__
        else:
            name_or_path = function_caller_module.__file__.replace("/", ".")
            # Remove .py extension
            name_or_path = Path(name_or_path).with_suffix("")

    else:
        name_or_path = function_caller_module.__name__

    log_path_map = {
        "name": name_or_path,
        "version": __version__,
        "date": datetime.now(timezone.utc),
    }

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)

    if log_dir is not None:
        log_paths = []
        for output_file, file_level in zip(output_files, file_levels, strict=True):
            log_path_map["levelname"] = logging._levelToName[file_level]
            log_path = log_dir / output_file.format_map(log_path_map)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            f_handler = logging.FileHandler(log_path)
            f_handler.setLevel(file_level)
            f_handler.setFormatter(f_format)

            # Add handlers to the logger
            root_logger.addHandler(f_handler)

        for log_path in log_paths:
            logger.info(f"Logging to {log_path}")


def main():
    logger.info("Hello, world!")
    raise Exception("Test exception")


if __name__ == "__main__":
    try:
        setup_logging()
        main()
    except Exception:
        logger.exception("Exception occurred")
