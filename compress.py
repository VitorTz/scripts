#!/usr/bin/env python3
from multiprocessing.pool import ThreadPool
from pathlib import Path
from PIL import Image
import os
import sys

def convert_to_webp(
    path: Path,
    output: Path | None = None,
    delete_input: bool = True,
    quality: int = 80,
    lossless: bool = False,
    force_compress: bool = True
) -> Path | None:       
    if output is None: output = path.with_suffix(".webp")

    if path.suffix == ".webp":
        if force_compress:
            with Image.open(path) as img:
                img.save(
                    output,
                    format='WEBP',
                    quality=quality,
                    lossless=lossless
                )
            print(f"[IMAGE {path} COMPRESSED]")
        return path
    
    try:
        with Image.open(path) as img:
            img.save(
                output,
                format='WEBP',
                quality=quality,
                lossless=lossless                
            )
        
        if delete_input and path.suffix != ".webp":
            os.remove(str(path))

        print(f"[IMAGE {path} CONVERTED TO WEBP]")
        return output
    except Exception as e:        
        print(f"[COULD NOT COVERT {path} TO WEBP] {e}")


def convert_dir(dir_path: Path) -> None:
    with ThreadPool(4) as pool:
        pool.map(convert_to_webp, [x for x in dir_path.iterdir() if x.is_file()])


def main():
    path = Path(sys.argv[1])
    if path.is_dir():
        convert_dir(path)
    elif path.is_file():
        convert_to_webp(path)

if __name__ == "__main__":
    main()
