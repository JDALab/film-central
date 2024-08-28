from __future__ import annotations
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from typing import Optional

    from bs4 import Tag
    from httpx import Response
    from mov_cli.config import Config
    from mov_cli.http_client import HTTPClient
    from mov_cli.scraper import ScraperOptionsT

from mov_cli import Scraper
from mov_cli.utils import EpisodeSelector
from mov_cli.media import Metadata, MetadataType, Multi, Single

from httpx import ReadTimeout

from .query_optimizer import optimize_query

__all__ =(
    "BFlix",
)

BFLIX_HOST = "https://w1.nites.is"

class BFlix(Scraper):
    def __init__(
        self, 
        config: Config, 
        http_client: HTTPClient, 
        options: ScraperOptionsT = None
    ) -> None:
        super().__init__(
            config = config,
            http_client = http_client,
            options = options
        )

    def search(self, query: str, limit: int | None = None) -> Iterable[Metadata]:
        if query == "*":
            query = "" # Will return latest content.

        response = self.__request_and_handle_timeouts(
            method = "GET",
            url = BFLIX_HOST,
            params = {"s": optimize_query(query)}
        )

        soup = self.soup(response.text)

        search_results = soup.select("article.post.dfx.fcl.movies.more-infos")

        for result in search_results:
            title = result.find("div", {"class": "entry-title"}).text
            # description = result.find("div", {"class": "entry-content"}).find("p").text
            watch_url = result.find("li", {"class": "fg1"}).find("a", {"class": "btn"})["href"]
            image_url = result.find("div", {"class": "post-thumbnail"}).find("img")["data-src"] # Not every result has an image.
            quality_or_type = result.find("span", {"class": "quality"}).text # We use it to determine between multi media or single though.
            year = result.find("span", {"class": "year"}).text

            yield Metadata(
                id = watch_url,
                title = title,
                type = MetadataType.MULTI if quality_or_type == "TV-Show" else MetadataType.SINGLE,
                image_url = "https:" + image_url.replace("w342", "w500"),
                year = year
            )

    def scrape(self, metadata: Metadata, episode: EpisodeSelector) -> Optional[Multi | Single]:
        response = self.__request_and_handle_timeouts(
            method = "GET",
            url = metadata.id
        )

        soup = self.soup(response.text)

        iframe_tag = soup.find("div", {"id": "options-0"}).find("iframe")

        stream_url = self.__grab_bflix_player_stream_url(iframe_tag)

        media = None

        if metadata.type == MetadataType.MULTI:
            ... # TODO: handle tv series...

        else:
            media = Single(
                url = stream_url,
                title = metadata.title,
                referrer = "https://bflix.gs/"
            )

        return media

    def __request_and_handle_timeouts(self, method: str, url: str, hangs: int = 5, **kwargs) -> Response:
        """
        For some reason some requests to this site randomly hang then fail.
        This function should handle that until 5 hangs or what is specified is reached.
        """
        try:
            response = self.http_client.request(
                method = method,
                url = url,
                **kwargs
            )

        except ReadTimeout as e:
            self.logger.warning(
                "Bflix request timed out! This is unusually normal for bflix so I'm going to retry..."
            )

            if hangs == 0:
                self.logger.critical(
                    "We tried to handle the timeouts but this time bflix timed out more than expected. Report this!"
                )

                raise e

            response = self.__request_and_handle_timeouts(method, url, hangs - 1, **kwargs)

        return response

    def __grab_bflix_player_stream_url(self, player_iframe: Tag) -> str:
        nites_video_embed_response = self.__request_and_handle_timeouts(
            method = "GET",
            url = player_iframe["data-lazy-src"]
        )

        nites_video_embed_soup = self.soup(nites_video_embed_response.text)

        bflix_video_embed_tag = nites_video_embed_soup.find("iframe")

        bflix_video_embed_response = self.__request_and_handle_timeouts(
            method = "GET",
            url = bflix_video_embed_tag["src"]
        )

        bflix_video_embed_soup = self.soup(bflix_video_embed_response.text)

        # WTF THE ID IS EMBEDDED IN THE TITLE TAG!
        my_file_storage_id: str = bflix_video_embed_soup.find("head").find("title").text

        return f"https://myfilestorage.xyz/{my_file_storage_id}.mp4"