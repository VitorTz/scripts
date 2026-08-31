#!/usr/bin/env python3
"""
Download a YouTube video's (or playlist's) audio as MP3 at the best
available quality.

Requires:
    pip install yt-dlp
    ffmpeg installed and on PATH (apt install ffmpeg / brew install ffmpeg)

Usage:
    # vídeo único (aceita ID ou URL completa)
    python yt_to_mp3.py <url_ou_id> [output_dir]

    # playlist inteira (detecta automaticamente se a URL tiver "list=",
    # ou force com --playlist)
    python yt_to_mp3.py <playlist_url> [output_dir] --playlist

    # forçar baixar só o vídeo mesmo que a URL tenha "list="
    python yt_to_mp3.py <url> [output_dir] --no-playlist
"""

import argparse
from pathlib import Path

from yt_dlp import YoutubeDL


def build_url(value: str) -> str:
    """Aceita tanto uma URL completa quanto apenas o ID do vídeo."""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://www.youtube.com/watch?v={value}"


def download_mp3(url_or_id: str, output_dir: str = ".", playlist: bool = False) -> None:
    url = build_url(url_or_id)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if playlist:
        # organiza em uma subpasta com o nome da playlist, numerando as faixas
        outtmpl = f"{output_dir}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"
    else:
        outtmpl = f"{output_dir}/%(title)s.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",  # 0 = melhor VBR
            }
        ],
        "noplaylist": not playlist,
        "ignoreerrors": playlist,  # se um vídeo da playlist falhar, continua os outros
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa áudio do YouTube em MP3 (vídeo único ou playlist).")
    parser.add_argument("url", help="URL/ID do vídeo, ou URL da playlist")
    parser.add_argument("output_dir", nargs="?", default="/mnt/HD/Music", help="Pasta de saída")
    parser.add_argument(
        "--playlist",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Baixar a playlist inteira. Se omitido, é detectado automaticamente pela URL (presença de 'list=').",
    )
    args = parser.parse_args()

    playlist = args.playlist
    if playlist is None:
        playlist = "list=" in args.url

    download_mp3(args.url, args.output_dir, playlist=playlist)


if __name__ == "__main__":
    main()