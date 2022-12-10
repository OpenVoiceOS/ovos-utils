import socket

import requests

from ovos_utils.log import LOG


def get_network_tests_config():
    """Get network_tests object from mycroft.configuration."""
    from ovos_config import Configuration
    config = Configuration()
    return config.get(
        "network_tests",
        {
            "ip_url": 'https://api.ipify.org',
            "dns_primary": "1.1.1.1",
            "dns_secondary": "8.8.8.8",
            "web_url": "https://nmcheck.gnome.org/check_network_status.txt",
            "web_url_secondary": "https://checkonline.home-assistant.io/online.txt"
        }
    )


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
    return requests.get(cfg["ip_url"]).text


def is_connected_dns(host=None, port=53, timeout=3):
    """Check internet connection by connecting to DNS servers
    Returns:
        True if internet connection can be detected
    """

    if host is None:
        cfg = get_network_tests_config()
        return is_connected_dns(cfg["dns_primary"]) or \
               is_connected_dns(cfg["dns_secondary"])

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
        return is_connected_http(cfg["web_url"]) or \
               is_connected_http(cfg["web_url_secondary"])

    try:
        status = requests.head(host).status_code
        return True
    except:
        pass
    return False


def is_connected():
    return any((is_connected_dns(), is_connected_http()))


def check_captive_portal(url="http://start.mycroft.ai/portal-check.html",
                         expected_text="<title>Portal Check</title>") -> bool:
    """Returns True if a captive portal page is detected"""
    captive_portal = False

    try:
        # We need to check a site that doesn't use HTTPS
        html_doc = requests.get(url).text

        # If something different is in the html, we likely were redirected
        # to the portal page.
        if expected_text not in html_doc:
            captive_portal = True
    except Exception:
        LOG.exception("Error checking for captive portal")

    return captive_portal

