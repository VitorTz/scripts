#!/usr/bin/env python3
"""
Altera a tag de artista (e opcionalmente álbum/artista do álbum) de todas
as músicas de uma pasta, de uma vez só, em paralelo.

Requires:
    pip install mutagen

Usage:
    # define o artista em todos os mp3 da pasta (não entra em subpastas)
    python set_artist_tag.py /mnt/HD/Music/AlgumaPlaylist --artist "Nome do Artista"

    # entra em subpastas também (útil pra pastas de playlist)
    python set_artist_tag.py /mnt/HD/Music --artist "Nome do Artista" --recursive

    # de quebra, também define álbum / artista do álbum
    python set_artist_tag.py ./pasta --artist "Fulano" --album "Nome do Álbum" --album-artist "Fulano"

    # só mostra o que seria alterado, sem gravar nada
    python set_artist_tag.py ./pasta --artist "Fulano" --dry-run

    # outras extensões além de mp3 (m4a, flac, ogg, opus...)
    python set_artist_tag.py ./pasta --artist "Fulano" --ext mp3,m4a,flac

    # sobrescrever o número de threads (padrão: 2x os núcleos disponíveis)
    python set_artist_tag.py ./pasta --artist "Fulano" --workers 8
"""
import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import mutagen


def default_workers() -> int:
    """2x o número de núcleos disponíveis para o processo (respeita cgroups/afinidade em containers)."""
    try:
        cores = len(os.sched_getaffinity(0))
    except AttributeError:  # macOS/Windows não têm sched_getaffinity
        cores = os.cpu_count() or 1
    return max(1, cores * 2)


def iter_audio_files(folder: Path, extensions: set[str], recursive: bool):
    pattern = "**/*" if recursive else "*"
    for path in sorted(folder.glob(pattern)):
        if path.is_file() and path.suffix.lower().lstrip(".") in extensions:
            yield path


def set_tags(path: Path, artist: str, album: str | None, album_artist: str | None, dry_run: bool) -> tuple[bool, str]:
    try:
        audio = mutagen.File(path, easy=True)
        if audio is None:
            return False, f"[ignorado] {path.name}: formato não reconhecido pelo mutagen"

        if audio.tags is None:
            audio.add_tags()

        audio["artist"] = artist
        if album is not None:
            audio["album"] = album
        if album_artist is not None:
            audio["albumartist"] = album_artist

        if dry_run:
            msg = f"[dry-run] {path.name} -> artist={artist!r}"
            if album is not None:
                msg += f", album={album!r}"
            if album_artist is not None:
                msg += f", album_artist={album_artist!r}"
            return True, msg

        audio.save()
        return True, f"[ok] {path.name}"
    except Exception as e:
        return False, f"[erro] {path.name}: {e}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Altera a tag de artista (e opcionalmente álbum) de todas as músicas de uma pasta, em paralelo."
    )
    parser.add_argument("folder", help="Pasta com os arquivos de música")
    parser.add_argument("--artist", required=True, help="Nome do artista a gravar em todos os arquivos")
    parser.add_argument("--album", default=None, help="Opcional: também define a tag de álbum")
    parser.add_argument("--album-artist", default=None, help="Opcional: também define a tag de artista do álbum")
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Entrar em subpastas também (ex.: pastas de playlist criadas pelo yt_to_mp3.py)",
    )
    parser.add_argument(
        "--ext",
        default="mp3",
        help="Extensões a processar, separadas por vírgula (padrão: mp3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Só mostra o que seria alterado, sem gravar nada",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Número de threads em paralelo (padrão: 2x os núcleos disponíveis)",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        parser.error(f"pasta não encontrada: {folder}")

    extensions = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}

    files = list(iter_audio_files(folder, extensions, args.recursive))
    if not files:
        print(f"Nenhum arquivo com extensão {sorted(extensions)} encontrado em {folder}")
        return

    workers = args.workers if args.workers and args.workers > 0 else default_workers()
    print(
        f"{len(files)} arquivo(s) encontrado(s) em {folder}"
        f"{' (recursivo)' if args.recursive else ''} — processando com {workers} threads:"
    )

    changed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_path = {
            executor.submit(set_tags, path, args.artist, args.album, args.album_artist, args.dry_run): path
            for path in files
        }
        for future in as_completed(future_to_path):
            ok, msg = future.result()
            print(f"  {msg}")
            if ok:
                changed += 1

    action = "seriam alterados" if args.dry_run else "alterados"
    print(f"\n{changed}/{len(files)} arquivo(s) {action}.")


if __name__ == "__main__":
    main()