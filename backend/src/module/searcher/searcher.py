import json
from typing import TypeAlias

from module.models import Bangumi, RSSItem, Torrent
from module.network import RequestContent
from module.manager.torrent import TorrentManager
from module.rss import RSSAnalyser

from .provider import search_url

SEARCH_KEY = [
    "group_name",
    "title_raw",
    "season_raw",
    "subtitle",
    "source",
    "dpi",
]

BangumiJSON: TypeAlias = str


class SearchTorrent(RequestContent, RSSAnalyser, TorrentManager):
    def search_torrents(self, rss_item: RSSItem) -> list[Torrent]:
        return self.get_torrents(rss_item.url)
        # torrents = self.get_torrents(rss_item.url)
        # return torrents

    def analyse_keyword(
        self, keywords: list[str], site: str = "mikan", limit: int = 5
    ) -> BangumiJSON:
        rss_item = search_url(site, keywords)
        torrents = self.search_torrents(rss_item)
        # yield for EventSourceResponse (Server Send)
        exist_list = []
        for torrent in torrents:
            if len(exist_list) >= limit:
                break
            bangumi = self.torrent_to_data(torrent=torrent, rss=rss_item)
            if bangumi:
                special_link = self.special_url(bangumi, site).url
                if special_link not in exist_list:
                    bangumi.rss_link = special_link
                    exist_list.append(special_link)
                    yield json.dumps(bangumi.dict(), separators=(",", ":"))

    @staticmethod
    def special_url(data: Bangumi, site: str) -> RSSItem:
        keywords = [getattr(data, key) for key in SEARCH_KEY if getattr(data, key)]
        url = search_url(site, keywords)
        return url
    
    def build_search_url(self, data: Bangumi, site: str) -> RSSItem:
        keywords = []
        keywords.append(data.official_title)
        if(int(data.season) != 1):
            keywords.append(data.season_raw)
        url = search_url(site, keywords)
        return url

    def search_season(self, data: Bangumi, site: str = "mikan") -> list[Torrent]:
        rss_item = self.build_search_url(data, site)
        torrents = self.search_torrents(rss_item)
        new_torrents = []
        for item1 in torrents:
            if(str(data.season_raw) in item1.name or data.season_raw == None):
                res = self.refine_torrent(data, item1)
                if(res):
                    new_torrents.append(res)
        return new_torrents