from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

    from bs4 import ResultSet, Tag
    from mov_cli import Config
    from mov_cli.http_client import HTTPClient
    from mov_cli.scraper import ScraperOptionsT

import re

from mov_cli import utils
from mov_cli.scraper import Scraper
from mov_cli import Multi, Single, Metadata, MetadataType

__all__ = ("VadapavScraper",)

class VadapavScraper(Scraper):
    def __init__(self, config: Config, http_client: HTTPClient, options: Optional[ScraperOptionsT] = None) -> None:
        self.base_url = "https://vadapav.mov"
        super().__init__(config, http_client, options)

    def search(self, query: str, limit: Optional[int]) -> Iterable[Metadata]:
        limit = 20 if limit is None else limit

        search_url = f"{self.base_url}/s/{query}"
        search_html = self.http_client.get(search_url)
        search_results_soup = self.soup(search_html)
        # In this site, all movies are appended with its release year.
        # So it can be used as an inexpensive way to determine the type of media
        # movie_pattern = r".*\(\d{4}\)$"

        index = 0

        for search_result_item in search_results_soup.find_all("a", {"class": "directory-entry"}):
            if index > limit:
                break

            item_url = search_result_item.get("href")

            r = self.http_client.get(self.base_url + item_url)
            item_page = self.soup(r.text)

            item_directory_path: ResultSet[Tag] = item_page.find("div", {"class": "directory"}).find("div").find_all("span")

            item_type = None
            item_name = None
            item_year = None

            for dir_path in item_directory_path:

                if dir_path.text.startswith(("Movies",)):
                    item_type = MetadataType.SINGLE
                    item_year = search_result_item.string[-5:-1]
                    item_name = search_result_item.string[:-6]
                    break

                elif dir_path.text.startswith(("TV", "TV Shows")):
                    item_type = MetadataType.MULTI
                    item_name = search_result_item.string
                    break

            if item_type is None:
                continue

            index =+ 1

            yield Metadata(
                id=item_url.strip("/"),
                title=item_name,
                type=item_type,
                year=item_year,
            )

    def scrape_episodes(self, metadata: Metadata):
        seasons_html = self.http_client.get(f"{self.base_url}/{metadata.id}")
        seasons_soup = self.soup(seasons_html)
        season_dirs = [
            dir
            for dir in seasons_soup.find_all("a", {"class": "directory-entry"})
            if "Season" in dir.string
        ]
        result = {}
        for i, season in enumerate(season_dirs):
            season_html = self.http_client.get(self.base_url + season.get("href"))
            season_soup = self.soup(season_html)
            episodes_entries = [
                episode
                for episode in season_soup.find_all("a", {"class": "file-entry"})
                if episode.string[-4:] not in [".srt", ".txt"]
            ]
            result[i + 1] = len(episodes_entries)
        return result

    def extract_resolution(self, filename):
        # Regular expression to extract resolution information
        match = re.search(r"(\d+)p|4K", filename)
        if match:
            if match.group(1):  # If a numeric resolution is found (e.g., "720p")
                return int(match.group(1))
            else:  # If "4K" is found
                return 2160  # Assumed resolution for 4K
        else:
            return 0  # Default to 0 if resolution is not found

    def scrape(self, metadata: Metadata, episode: utils.EpisodeSelector) -> Multi | Single:

        if metadata.type == MetadataType.SINGLE:
            mov_dir_html = self.http_client.get(f"{self.base_url}/{metadata.id}")
            movie_soup = self.soup(mov_dir_html)
            mov_files = [
                x
                for x in movie_soup.find_all("a", {"class": "file-entry"})
                if x.string[-4:] not in [".srt", ".txt"]
            ]

            subtitles = [
                x
                for x in movie_soup.find_all("a", {"class": "file-entry"})
                if x.string[-4:] == ".srt"
            ]
            subtitle_url = (
                {
                    "en": self.base_url
                    + (subtitles[0].get("data-href") or subtitles[0].get("href"))
                }
                if subtitles
                else None
            )

            # Always select greatest resolution when there are multiple files
            # Starting with a resolution that's lower than any possible resolution
            movie_url, max_resolution = "", -1
            for mov_file in mov_files:
                resolution = self.extract_resolution(mov_file.string)
                if resolution > max_resolution:
                    max_resolution = resolution
                    movie_url = mov_file.get("data-href") or mov_file.get("href")

            series_url = self.base_url + movie_url

            return Single(
                series_url,
                title=metadata.title,
                referrer=self.base_url,
                year=metadata.year,
                subtitles=subtitle_url,
            )

        season_no = int(episode.season)
        episode_no = int(episode.episode)

        season_str = "S" + str(season_no) if season_no > 9 else "S0" + str(season_no)
        season_dir_name = (
            "Season " + str(season_no) if season_no > 9 else "Season 0" + str(season_no)
        )
        episode_str = (
            "E" + str(episode_no) if episode_no > 9 else "E0" + str(episode_no)
        )

        series_dir_html = self.http_client.get(f"{self.base_url}/{metadata.id}")
        series_soup = self.soup(series_dir_html)
        season_directories = series_soup.find_all("a", {"class": "directory-entry"})[1:]

        for season_dir in season_directories:
            if season_dir.string == season_dir_name:
                season_dir_html = self.http_client.get(
                    self.base_url + season_dir.get("href")
                )
                season_soup = self.soup(season_dir_html)
                episode_files = [
                    file_entry
                    for file_entry in season_soup.find_all("a", {"class": "file-entry"})
                    if file_entry.string[-4:] != ".srt"
                ]
                break

        for episode_file in episode_files:
            if season_str + episode_str in episode_file.string.upper():
                episode_url = self.base_url + (
                    episode_file.get("data-href") or episode_file.get("href")
                )
                break

        return Multi(
            episode_url,
            title=metadata.title,
            referrer=self.base_url,
            episode=episode,
            subtitles=None,
        )
