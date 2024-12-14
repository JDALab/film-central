from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Dict, Generator, Any

    from mov_cli import Config
    from mov_cli.http_client import HTTPClient
    from mov_cli.scraper import ScraperOptionsT

from mov_cli import Single, Multi, Metadata, MetadataType
from mov_cli.scraper import Scraper
from mov_cli.utils import EpisodeSelector

import re

__all__ = (
    "CatFlix",
)

class CatFlix(Scraper):
    def __init__(self,
        config: Config,
        http_client: HTTPClient,
        options: Optional[ScraperOptionsT] = None
    ) -> None:
        self.BASE_URL = "https://catflix.su"

        super().__init__(config, http_client, options)

    def search(self, query: str, limit: int = 20) -> Generator[Metadata, Any, None]:
        response = self.http_client.get(f"{self.BASE_URL}/?s={query}")
        soup = self.soup(response.text)

        # TODO: Limit search results
        search_results = soup.select("li.flex.relative.rounded-lg")
        for result in search_results:
            title = result.h2.string.strip()
            watch_url = result.a.get("href")
            image_url = result.img.get("src")
            year = result.find("span", class_=None).string.strip()

            id = watch_url.split("/")[-2]
            media_type = MetadataType.SINGLE if "/movies/" in watch_url else MetadataType.MULTI
            
            yield Metadata(
                id=id,
                title=title,
                type=media_type,
                image_url=image_url,
                year=year
            )


    def scrape_episodes(self, metadata: Metadata) -> Dict[int, int] | Dict[None, int]:
        response = self.http_client.get(f"{self.BASE_URL}/series/{metadata.id}/")
        soup = self.soup(response.text)

        episodes_dict = {}
        search_results = soup.select("div.grid.grid-cols-2")
        for i, season in enumerate(search_results):
            episodes_dict[i + 1] = len(season.find_all("article"))

        return episodes_dict
    
    # TODO: Subtitles support
    # TODO: Error handling
    def scrape(self, metadata: Metadata, episode: EpisodeSelector) -> Single | Multi:
        ep, season = episode.episode, episode.season
        media_url = \
            f"{self.BASE_URL}/movies/{metadata.id}/" if metadata.type == MetadataType.SINGLE else \
            f"{self.BASE_URL}/episodes/{metadata.id}-{season}x{ep}/"
        
        response = self.http_client.get(media_url)
        soup = self.soup(response.text)

        iframe_tag = soup.find("iframe", src=re.compile(r'https://turbovid\.eu/embed/*+'))
        iframe_src = iframe_tag.get("src")

        response = self.http_client.get(iframe_src)
        embed_soup = self.soup(response.text)

        script_vars_str = embed_soup.find("script", string=re.compile(r'(apkey|xxid)')).string
        vars_pattern = re.compile(r'(apkey|xxid) *= *"(.+)"')
        script_vars = { var: value for var, value in vars_pattern.findall(script_vars_str) }

        # I think `apkey` always has the same value, but better safe than sorry.
        apkey, xxid = script_vars.get("apkey"), script_vars.get("xxid")

        JUICE_KEY_URL = "https://turbovid.eu/api/cucked/juice_key"
        JUICE_DATA_URL = f"https://turbovid.eu/api/cucked/the_juice/?{apkey}={xxid}"

        response = self.http_client.get(JUICE_KEY_URL)
        key_data = response.json()
        juice_key = key_data.get("juice")

        response = self.http_client.get(JUICE_DATA_URL)
        juice_data = response.json()
        hex_data = juice_data.get("data")

        stream_url = self.__decrypt(hex_data, juice_key)

        if metadata.type == MetadataType.SINGLE:
            return Single(
                url=stream_url,
                title=metadata.title,
                referrer="https://turbovid.eu/",
                year=metadata.year
            )

        return Multi(
            url=stream_url,
            title=metadata.title,
            episode=episode,
            referrer="https://turbovid.eu/"
        )

    def __decrypt(self, cyphertext: str, key: str) -> str:
        decimal_cypher = [int(cyphertext[i:i+2], base=16) \
                             for i in range(0, len(cyphertext), 2)]

        plaintext = ""
        for i in range(len(decimal_cypher)):
            plaintext += chr(decimal_cypher[i] ^ ord(key[i % len(key)]))
        return plaintext
