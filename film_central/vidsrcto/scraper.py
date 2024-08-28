from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any, Literal, Generator, Optional

    from httpx import Response

    from mov_cli import Config
    from mov_cli.http_client import HTTPClient
    from mov_cli.scraper import ScraperOptionsT

from mov_cli.scraper import Scraper
from mov_cli.utils import EpisodeSelector
from mov_cli import Multi, Single, Metadata, MetadataType

import base64
from urllib.parse import unquote
from .ext import VidPlay
from mov_cli.utils.scraper import TheMovieDB

__all__ = ("VidSrcToScraper", )


class VidSrcToScraper(Scraper):
    def __init__(self, config: Config, http_client: HTTPClient, options: Optional[ScraperOptionsT] = None) -> None:
        self.base_url = "https://vidsrc.to"
        self.sources = self.base_url + "/ajax/embed/episode/{}/sources"
        self.source = self.base_url + "/ajax/embed/source/{}"
        self.tmdb = TheMovieDB(http_client)
        self.referrer = "https://vid2v11.site"

        super().__init__(config, http_client, options)

    def search(self, query: str, limit: int = 20) -> Generator[Metadata, Any, None]:

        for search_result in self.tmdb.search(query, limit):
            embed_response = self.__get_embed(search_result, EpisodeSelector())

            if embed_response.status_code == 404: # don't include media that isn't available on the provider.
                continue

            yield search_result

    def scrape_episodes(self, metadata: Metadata) -> Dict[int, int] | Dict[None, Literal[1]]:
        return self.tmdb.scrape_episodes(metadata)

    def scrape(self, metadata: Metadata, episode: EpisodeSelector) -> Optional[Multi | Single]:
        embed_response = self.__get_embed(metadata, episode)

        soup = self.soup(embed_response)

        id = soup.find('a', {'data-id': True})

        if not id:
            return None

        id = id.get("data-id", None)

        sources = self.http_client.get(self.sources.format(id)).json()

        vidplay_id = None

        for source in sources["result"]:
            if source["title"] == "F2Cloud" or source["title"] == "Vidplay":
                vidplay_id = source["id"]

        if not vidplay_id:
            return None

        get_source = self.http_client.get(self.source.format(vidplay_id)).json()["result"]["url"]

        vidplay_url = self.__deobf(get_source)

        vidplay = VidPlay(self.http_client)

        url = vidplay.resolve_source(vidplay_url, self.referrer)[0]

        if url is None:
            return None

        if metadata.type == MetadataType.MULTI:
            return Multi(
                url = url,
                title = metadata.title,
                episode = episode,
                referrer = self.referrer
            )

        return Single(
            url = url,
            title = metadata.title,
            year = metadata.year,
            referrer = self.referrer
        )

    def __get_embed(self, metadata: Metadata, episode: EpisodeSelector) -> Response:
        media_type = "tv" if metadata.type == MetadataType.MULTI else "movie"

        url = f"{self.base_url}/embed/{media_type}/{metadata.id}"

        if metadata.type == MetadataType.MULTI:
            url += f"/{episode.season}/{episode.episode}"

        return self.http_client.get(url)

    def __deobf(self, encoded_url: str) -> str | bool:
        # This is based on https://github.com/Ciarands/vidsrc-to-resolver/blob/dffa45e726a4b944cb9af0c9e7630476c93c0213/vidsrc.py#L16
        # Thanks to @Ciarands!
        standardized_input = encoded_url.replace('_', '/').replace('-', '+')
        binary_data = base64.b64decode(standardized_input)

        key_bytes = bytes("WXrUARXb1aDLaZjI", 'utf-8')
        s = bytearray(range(256))
        j = 0

        for i in range(256):
            j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
            s[i], s[j] = s[j], s[i]

        decoded = bytearray(len(binary_data))
        i = 0
        k = 0

        for index in range(len(binary_data)):
            i = (i + 1) & 0xff
            k = (k + s[i]) & 0xff
            s[i], s[k] = s[k], s[i]
            t = (s[i] + s[k]) & 0xff

            if isinstance(binary_data[index], str):
                decoded[index] = ord(binary_data[index]) ^ s[t]
            elif isinstance(binary_data[index], int):
                decoded[index] = binary_data[index] ^ s[t]
            else:
                decoded = False

        return unquote(decoded.decode("utf-8"))