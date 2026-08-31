#!/usr/bin/env python3
"""
Download a YouTube video's (or playlist's) audio as MP3 at the best
available quality, com tags ID3 (título, artista, álbum, capa) embutidas.

Requires:
    pip install yt-dlp
    ffmpeg instalado e no PATH (apt install ffmpeg / brew install ffmpeg)

Usage:
    # vídeo único (aceita ID ou URL completa)
    python yt_to_mp3.py <url_ou_id> [output_dir]

    # playlist inteira (detecta automaticamente se a URL tiver "list=",
    # ou force com --playlist)
    python yt_to_mp3.py <playlist_url> [output_dir] --playlist

    # forçar baixar só o vídeo mesmo que a URL tenha "list="
    python yt_to_mp3.py <url> [output_dir] --no-playlist

    # desativar a tentativa de separar "Artista - Título" do nome do vídeo
    python yt_to_mp3.py <url> [output_dir] --no-split-title
"""
import argparse
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.postprocessor import MetadataParserPP


def build_url(value: str) -> str:
    """Aceita tanto uma URL completa quanto apenas o ID do vídeo."""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://www.youtube.com/watch?v={value}"


def download_mp3(
    url_or_id: str,
    output_dir: str = ".",
    playlist: bool = False,
    split_title: bool = True,
) -> None:
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
        # baixa a thumbnail para poder embuti-la como capa no mp3
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",  # 0 = melhor VBR
            },
            {
                # grava título/artista/álbum/data etc. como tags ID3
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                # embute a thumbnail baixada como capa (APIC) do mp3 e
                # apaga o arquivo de imagem solto depois de embutir
                "key": "EmbedThumbnail",
                "already_have_thumbnail": False,
            },
        ],
        "noplaylist": not playlist,
        "ignoreerrors": playlist,  # se um vídeo da playlist falhar, continua os outros
    }

    with YoutubeDL(ydl_opts) as ydl:
        if split_title:
            # Muitos vídeos musicais seguem o padrão "Artista - Título" no
            # nome do vídeo. Isso extrai esses campos para as tags
            # artist/title. Quando o vídeo é do YouTube Music, o próprio
            # extractor já entrega artist/album/track corretos e esse passo
            # simplesmente não encontra o padrão " - " e não faz nada.
            ydl.add_post_processor(
                MetadataParserPP(
                    ydl,
                    [(MetadataParserPP.Actions.INTERPRET, "title", "%(artist)s - %(title)s")],
                ),
                when="pre_process",
            )

        if playlist:
            # usa o nome da playlist como tag de álbum
            ydl.add_post_processor(
                MetadataParserPP(
                    ydl,
                    [(MetadataParserPP.Actions.INTERPRET, "playlist_title", "%(album)s")],
                ),
                when="pre_process",
            )

        ydl.download([url])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa áudio do YouTube em MP3 com metadados (vídeo único ou playlist)."
    )
    parser.add_argument("url", help="URL/ID do vídeo, ou URL da playlist")
    parser.add_argument("output_dir", nargs="?", default="/mnt/HD/Music", help="Pasta de saída")
    parser.add_argument(
        "--playlist",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Baixar a playlist inteira. Se omitido, é detectado automaticamente pela URL (presença de 'list=').",
    )
    parser.add_argument(
        "--split-title",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Tentar separar 'Artista - Título' do nome do vídeo para as tags (padrão: ativado).",
    )
    args = parser.parse_args()

    playlist = args.playlist
    if playlist is None:
        playlist = "list=" in args.url

    download_mp3(args.url, args.output_dir, playlist=playlist, split_title=args.split_title)


if __name__ == "__main__":
    main()
