#!/usr/bin/env python3
"""
Baixa o vídeo PRINCIPAL de uma página, ignorando vídeos recomendados/relacionados
exibidos na lateral ou abaixo do player.

Estratégia:
  1. Tenta usar yt-dlp — suporta centenas de sites e já sabe identificar
     corretamente o vídeo principal da página (ignora miniaturas de
     "recomendados", que normalmente são apenas links, não players).
  2. Se yt-dlp não reconhecer o site, cai para um extrator HTML genérico que
     procura tags <video>/<source> e meta tags og:video, descartando qualquer
     coisa dentro de contêineres com classes/ids típicos de
     "relacionados" / "sidebar" / "recomendados" / "up next".

Uso:
    python baixar_video.py "https://exemplo.com/pagina-do-video"
    python baixar_video.py "https://exemplo.com/pagina-do-video" -o meu_video.mp4

Requisitos:
    pip install yt-dlp requests beautifulsoup4

Observação: baixe apenas conteúdo que você tem o direito de baixar (vídeos
próprios, de domínio público, com licença aberta, ou onde o site permite
explicitamente). Respeite os termos de uso do site e a legislação de
direitos autorais aplicável.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# --------------------------------------------------------------------------- #
# Estratégia 1: yt-dlp (recomendado — cobre a grande maioria dos sites)
# --------------------------------------------------------------------------- #

def baixar_com_ytdlp(url: str, saida: str | None) -> bool:
    """Tenta baixar o vídeo usando yt-dlp. Retorna True se conseguiu."""
    try:
        import yt_dlp
    except ImportError:
        print("[yt-dlp] biblioteca não instalada, pulando essa estratégia.")
        return False

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,  # baixa só o vídeo alvo, não listas/recomendados
        "outtmpl": saida or "%(title)s.%(ext)s",
        "quiet": False,
        "no_warnings": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except yt_dlp.utils.DownloadError as e:
        print(f"[yt-dlp] não conseguiu baixar: {e}")
        return False


# --------------------------------------------------------------------------- #
# Estratégia 2: extrator HTML genérico (fallback para sites não suportados)
# --------------------------------------------------------------------------- #

# Palavras-chave que indicam que um elemento é uma área de vídeos
# recomendados/relacionados, e não o player principal.
CLASSES_IGNORAR = re.compile(
    r"relacionad|recommend|suggest|sidebar|up-next|upnext|mais-vistos|"
    r"related|carousel|widget|thumbnail-list|playlist",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _dentro_de_area_ignorada(tag) -> bool:
    """Sobe na árvore HTML checando se algum ancestral parece ser uma
    área de vídeos recomendados/relacionados."""
    for ancestor in tag.parents:
        classes = ancestor.get("class")
        classes_str = " ".join(classes) if isinstance(classes, list) else str(classes or "")
        attrs = f"{classes_str} {ancestor.get('id') or ''}"
        if CLASSES_IGNORAR.search(attrs):
            return True
    return False


def _extrair_candidatos(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidatos = []

    # 1) Meta tags og:video / og:video:url — quase sempre apontam para o vídeo principal
    for meta_name in ("og:video", "og:video:url", "og:video:secure_url", "twitter:player:stream"):
        tag = soup.find("meta", property=meta_name) or soup.find("meta", attrs={"name": meta_name})
        if tag and tag.get("content"):
            candidatos.append(urljoin(base_url, tag["content"]))

    # 2) Tags <video> (e seus <source>) fora de áreas de recomendados
    for video_tag in soup.find_all("video"):
        if _dentro_de_area_ignorada(video_tag):
            continue
        if video_tag.get("src"):
            candidatos.append(urljoin(base_url, video_tag["src"]))
        for source in video_tag.find_all("source"):
            if source.get("src"):
                candidatos.append(urljoin(base_url, source["src"]))

    # remove duplicados preservando ordem
    vistos = set()
    unicos = []
    for c in candidatos:
        if c not in vistos:
            unicos.append(c)
            vistos.add(c)
    return unicos


def baixar_com_extrator_generico(url: str, saida: str | None) -> bool:
    print("[genérico] buscando vídeo principal na página...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[genérico] falha ao acessar a página: {e}")
        return False

    candidatos = _extrair_candidatos(resp.text, url)
    if not candidatos:
        print("[genérico] nenhum vídeo principal encontrado na página.")
        return False

    video_url = candidatos[0]
    print(f"[genérico] vídeo principal identificado: {video_url}")

    nome_saida = saida or Path(urlparse(video_url).path).name or "video.mp4"
    if not Path(nome_saida).suffix:
        nome_saida += ".mp4"

    try:
        with requests.get(video_url, headers=HEADERS, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            baixado = 0
            with open(nome_saida, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
                        baixado += len(chunk)
                        if total:
                            pct = baixado * 100 // total
                            print(f"\rBaixando... {pct}% ({baixado // 1024} KB / {total // 1024} KB)", end="")
        print(f"\n[genérico] vídeo salvo em: {nome_saida}")
        return True
    except requests.RequestException as e:
        print(f"\n[genérico] falha ao baixar o vídeo: {e}")
        return False


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Baixa o vídeo principal de uma página web.")
    parser.add_argument("url", help="URL da página que contém o vídeo")
    parser.add_argument("-o", "--output", help="Nome/caminho do arquivo de saída", default=None)
    args = parser.parse_args()

    print(f"Alvo: {args.url}\n")

    if baixar_com_ytdlp(args.url, args.output):
        return

    print(
        "\nyt-dlp não conseguiu baixar (ou o site não é suportado). "
        "Tentando extrator genérico...\n"
    )

    if baixar_com_extrator_generico(args.url, args.output):
        return

    print(
        "\nNão foi possível baixar o vídeo principal automaticamente. "
        "Abra o DevTools do navegador (aba Network, filtro 'Media') enquanto "
        "o vídeo toca para localizar a URL manualmente."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()