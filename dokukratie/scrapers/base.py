from packaging.version import parse as versionparse

from .incremental import skip_while_testing as _skip_while_testing
from .operations import init


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

    def emit_configuration(self):
        """
        emit data for legislative terms and document types to next stage
        """
        init(self.context)

    def skip_while_testing(self, key=None, counter=-1):
        return _skip_while_testing(self.context, key, counter)
