import argparse
import logging
import json
import os
import shutil
import struct
import pathlib
import typing as T

import macholib.MachO
import macholib.util


def patch_dylib(
    dylib_path: pathlib.Path, root_to_replace: str, target_root: pathlib.Path
):
    """Replace dependencies with non-existing root

    Approach copied from https://github.com/pyinstaller/pyinstaller/blob/
    98aa4508455f3baaa8f15754ae5c95ee0e32806e/PyInstaller/depend/dylib.py#L338-L351
    """

    def _patch(path: str):
        path = pathlib.Path(path)
        try:
            path_relative = path.relative_to(root_to_replace)
        except ValueError:
            return  # dylib is not relative to root_to_replace
        path_target = target_root / path_relative
        assert path_target.exists(), f"Target {path_target} does not exist"
        print(path_target)
        return str(path_target)

    dylib = macholib.MachO.MachO(dylib_path)
    dylib.rewriteLoadCommands(_patch)

    try:
        with open(dylib.filename, "rb+") as f:
            for header in dylib.headers:
                f.seek(0)
                dylib.write(f)
            f.seek(0, 2)
            f.flush()
    except Exception:
        import traceback

        logging.error(traceback.format_exc())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch ")
    parser.add_argument("lib_dir")
    parser.add_argument("--replace", default="/tmp/vendor/lib")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    lib_dir = pathlib.Path(args.lib_dir).resolve()
    if not lib_dir.exists():
        raise FileNotFoundError(lib_dir)

    logging.info(
        f"Replacing `{args.replace}` with `{lib_dir}` for dependencies in {lib_dir}"
    )
    for dylib in macholib.util.iter_platform_files(lib_dir):
        patch_dylib(dylib, root_to_replace=args.replace, target_root=lib_dir)
