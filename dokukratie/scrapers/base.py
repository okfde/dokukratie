from packaging.version import parse as versionparse


class Version:
    """
    helper to easily compare via `if version < '1.2.3'`
    """

    def __init__(self, version):
        self.version = versionparse(version)

    def __str__(self):
        return str(self.version)

    def __eq__(self, version):
        return self.version == versionparse(version)

    def __ne__(self, version):
        return self.version != versionparse(version)

    def __gt__(self, version):
        return self.version > versionparse(version)

    def __ge__(self, version):
        return self.version >= versionparse(version)

    def __lt__(self, version):
        return self.version < versionparse(version)

    def __le__(self, version):
        return self.version <= versionparse(version)


class BaseScraper:
    def __init__(self, context):
        self.scraper = context.crawler.config["scraper"]
        self.name = self.scraper["name"]
        self.version = Version(self.scraper["version"])
        self.base_url = self.scraper["url"]
        self.context = context
