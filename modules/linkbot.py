from urllib.parse import urlparse
from html.parser import HTMLParser
import logging
import socket
import re
import fnmatch
import ipaddress
import aiohttp
from omnibot import Module


identity = lambda x: x
url_re = re.compile("\S+://\S+")
local_networks = ['127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '169.254.0.0/16']
log = logging.getLogger(__name__)


class LinkbotError(Exception):
    '''
    Basic exception that will cause linkbot to display an error message to the channel.
    '''
    def __init__(self, chan_message):
        super().__init__(chan_message)
        self.chan_message = chan_message


class HTMLTitleParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_start = False
        self.title_end = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if self.title_end: return
        if tag.lower() == "title":
            self.title_start = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.title_end = True

    def handle_data(self, data):
        if not self.title_end and self.title_start:
            self.title = data


class Linkbot(Module):
    default_args = {
        'blacklist': [],
        'max_urls': 1,
        'follow_local_urls': False,
    }

    async def on_message(self, channel, who, text):
        global url_re
        if not channel or not who:
            return
        matches = url_re.findall(text)
        urls = filter(self.is_valid_url, matches)
        count = 0
        for url in urls:
            if count >= self.args['max_urls']:
                break
            try:
                title = await self.get_title(url)
            except LinkbotError as ex:
                self.server.send_message(channel, "{}: {}".format(who, ex.chan_message))
            else:
                if not title:
                    continue
                if len(title) > 512:
                    title = title[0:512]
                self.server.send_message(channel, title)
                count += 1

    async def get_title(self, url):
        """
        Given a URL, attempts to get its title. If the URL does not match the content-type of text/*, None is
        returned.
        :returns: either a title, or None if the title couldn't be found.
        """
        # Get the request
        try:
            log.debug("getting title for %s", url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    text = await resp.text()
                    status = resp.status
                    headers = resp.headers
        except Exception as ex:
            log.debug("invalid URL: %s", ex)
            return None
        if status != 200:
            log.debug("invalid status code: %s", status)
            raise LinkbotError("{} error".format(status))
        elif not fnmatch.fnmatch(headers['content-type'], 'text/*'):
            log.debug("invalid content-type: %s", headers['content-type'])
            return None
        title_parser = HTMLTitleParser()
        title_parser.feed(text)
        return title_parser.title.strip()

    def is_valid_url(self, url):
        """
        Makes URL request to the given address. If they match the blacklist, or if their hosts resolve to an item in
        the blacklist, they are not followed. Also, if the URL does not parse, it is not followed.
        """
        global local_networks
        # make sure URL is valid
        try: url_parts = urlparse(url)
        except ValueError: return False # bad URL

        # make sure hostname is valid
        location = url_parts.netloc
        if not location: return False  # not a valid hostname

        # make sure hostname isn't blacklisted
        hostname = location if ':' in location else location.split(':')[0]
        if hostname in self.args['blacklist']: return False  # blacklisted

        # make sure address is valid
        try: addr = socket.gethostbyname(hostname)
        except socket.gaierror: return False  # bad hostname

        # make sure IP is not blacklisted
        if addr in self.args['blacklist']: return False  # blacklisted

        # make sure IP is not in local network if desired
        if not self.args['follow_local_urls']:
            ip = ipaddress.ip_address(addr)
            if not ip.is_global: log.warning("Linkbot tried to resolve non-global IP address: %s", addr)
            return ip.is_global
        else:
            # good URL
            return True


# TODO
# * ipv6 support
# * advanced pattern matching for links
# * max title length parameter

ModuleClass = Linkbot
