from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Iterable

if TYPE_CHECKING:
    from typing import Dict, Literal, Optional

    from mov_cli import Config
    from httpx import Response
    from mov_cli.http_client import HTTPClient
    from mov_cli.scraper import ScraperOptionsT

import re

from mov_cli.scraper import Scraper
from mov_cli import Multi, Single, Metadata, MetadataType
from mov_cli.utils.scraper import TheMovieDB
from mov_cli.utils import EpisodeSelector

import base64


__all__ = ("VidSrcMeScraper",)

class VidSrcMeScraper(Scraper):
    def __init__(self, config: Config, http_client: HTTPClient, options: Optional[ScraperOptionsT] = None) -> None:
        self.base_url = "https://vidsrc.net"
        self.tmdb = TheMovieDB(http_client)

        self.MAX_TRIES = 10
        super().__init__(config, http_client, options)

    def search(self, query: str, limit: int = 10) -> Iterable[Metadata]:
        for search_result in self.tmdb.search(query, limit):
            embed_response = self.__get_embed(search_result, EpisodeSelector())

            if embed_response.status_code == 404: # don't include media that isn't available on the provider.
                continue

            yield search_result

    def scrape_episodes(self, metadata: Metadata) -> Dict[int, int] | Dict[None, Literal[1]]:
        return self.tmdb.scrape_episodes(metadata)

    def __deobfstr(self, hash, index):
        result = ""
        for i in range(0, len(hash), 2):
            j = hash[i:i+2]
            result += chr(int(j, 16) ^ ord(index[i // 2 % len(index)]))
        return result

    def __get_url(self, prourl: str):
        url = None
        
        for _ in range(self.MAX_TRIES):
            prorcp = self.http_client.get(prourl, headers={"Referer": "https://vidsrc.stream/"})

            if prorcp.status_code == 503:
                continue
            
            hls_url = re.search(r'file:"([^"]*)"', prorcp.text).group(1)
            hls_url = re.sub(r'\/\/\S+?=', '', hls_url)[2:]     
            hls_url = re.sub(r"\/@#@\/[^=\/]+==", "", hls_url)

            hls_url = hls_url.replace('_', '/').replace('-', '+')

            try:
                hls_url = bytearray(base64.b64decode(hls_url))
                hls_url = hls_url.decode('utf-8')
            except UnicodeDecodeError:
                hls_url = None

            if hls_url is not None:
                url = hls_url
                break

        return url

    def __get_embed(self, metadata: Metadata, episode: EpisodeSelector) -> Response:
        media_type = "tv" if metadata.type == MetadataType.SERIES else "movie"

        url = f"{self.base_url}/embed/{media_type}/{metadata.id}"

        if metadata.type == MetadataType.SERIES:
            url += f"/{episode.season}/{episode.episode}"

        return self.http_client.get(url)

    def scrape(self, metadata: Metadata, episode: EpisodeSelector) -> Multi | Single:        
        for _ in range(self.MAX_TRIES):
            vidsrc = self.__get_embed(metadata, episode)

            if vidsrc.status_code != 503:
                break

        iframeurl = "https:" + self.soup(vidsrc).select("iframe#player_iframe")[0]["src"]

        for _ in range(self.MAX_TRIES):
            doc = self.http_client.get(iframeurl, headers={"Referer": vidsrc})

            if doc.status_code != 503:
                break

        doc = self.soup(doc)

        index = doc.select("body")[0]["data-i"]
        hash = doc.select("div#hidden")[0]["data-h"]

        srcrcp = "https:" + self.__deobfstr(hash, index).replace("vidsrc.stream", "vidsrc.net")

        for _ in range(self.MAX_TRIES):
            prourl = self.http_client.get(srcrcp, headers={"Referer": "https://vidsrc.stream/"}).headers.get("Location", None)

            if prourl is not None:
                break

        url = self.__get_url(prourl)

        if metadata.type == MetadataType.MOVIE:
            return Single(
                url = url,
                title = metadata.title,
                referrer = "https://vidsrc.stream/",
                year = metadata.year
            )

        return Multi(
            url = url,
            title = metadata.title,
            referrer = "https://vidsrc.stream/",
            episode = episode
        )