import socket

import requests

# backwards compat - was only out there for a couple alpha version
# TODO - remove next stable
from ovos_utils.process_utils import RuntimeRequirements as NetworkRequirements

from ovos_utils.log import LOG


_DEFAULT_TEST_CONFIG = {
    "ip_url": 'https://api.ipify.org',
    "dns_primary": "1.1.1.1",
    "dns_secondary": "8.8.8.8",
    "web_url": "http://nmcheck.gnome.org/check_network_status.txt",
    "web_url_secondary": "https://checkonline.home-assistant.io/online.txt",
    "captive_portal_url": "http://nmcheck.gnome.org/check_network_status.txt",
    "captive_portal_text": "NetworkManager is online"
    }


def get_network_tests_config():
    """Get network_tests object from mycroft.configuration."""
    from ovos_config import Configuration
    config = Configuration()
    return config.get("network_tests", _DEFAULT_TEST_CONFIG)


def get_ip():
    # taken from https://stackoverflow.com/a/28950776/13703283
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_external_ip():
    cfg = get_network_tests_config()
    return requests.get(cfg.get("ip_url") or _DEFAULT_TEST_CONFIG['ip_url']).text


def is_connected_dns(host=None, port=53, timeout=3):
    """Check internet connection by connecting to DNS servers
    Returns:
        True if internet connection can be detected
    """

    if host is None:
        cfg = get_network_tests_config()
        return is_connected_dns(cfg.get("dns_primary" or _DEFAULT_TEST_CONFIG['dns_primary'])) or \
            is_connected_dns(cfg.get("dns_secondary" or _DEFAULT_TEST_CONFIG['dns_secondary']))

    try:
        # connect to the host -- tells us if the host is actually reachable
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        return True
    except OSError:
        pass
    return False


def is_connected_http(host=None):
    """Check internet connection by connecting to some website
    Returns:
        True if connection attempt succeeded
    """
    if host is None:
        cfg = get_network_tests_config()
        return is_connected_http(cfg.get("web_url") or _DEFAULT_TEST_CONFIG['web_url']) or \
            is_connected_http(cfg.get("web_url_secondary") or _DEFAULT_TEST_CONFIG['web_url_secondary'])

    try:
        status = requests.head(host).status_code
        return True
    except:
        pass
    return False


def is_connected():
    return any((is_connected_dns(), is_connected_http()))


def check_captive_portal(host=None, expected_text=None) -> bool:
    """Returns True if a captive portal page is detected"""
    captive_portal = False

    if not host or not expected_text:
        cfg = get_network_tests_config()
        host = host or cfg.get("captive_portal_url") or _DEFAULT_TEST_CONFIG["captive_portal_url"]
        expected_text = expected_text or cfg.get("captive_portal_text") or _DEFAULT_TEST_CONFIG["captive_portal_text"]

    try:
        # We need to check a site that doesn't use HTTPS
        html_doc = requests.get(host).text
        # If something different is in the html, we likely were redirected
        # to the portal page.
        if expected_text not in html_doc:
            captive_portal = True
    except Exception:
        LOG.exception("Error checking for captive portal")

    return captive_portal

