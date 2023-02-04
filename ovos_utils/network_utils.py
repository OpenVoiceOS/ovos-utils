import socket
import requests
from dataclasses import dataclass


@dataclass
class NetworkRequirements:
    # to ensure backwards compatibility the default values require internet before skill loading
    # skills in the wild may assume this behaviour and require network on initialization
    # any ovos aware skills should change these as appropriate

    # xxx_before_load is used by skills service
    network_before_load: bool = True
    internet_before_load: bool = True

    # requires_xxx is currently purely informative and not consumed by core
    # this allows a skill to spec if it needs connectivity to handle utterances
    requires_internet: bool = True
    requires_network: bool = True

    # xxx_fallback is currently purely informative and not consumed by core
    # this allows a skill to spec if it has a fallback for temporary offline events, eg, by having a cache
    no_internet_fallback: bool = False
    no_network_fallback: bool = False


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
    return requests.get('https://api.ipify.org').text


def is_connected_dns(host="1.1.1.1"):
    try:
        # connect to the host -- tells us if the host is actually reachable
        socket.create_connection((host, 53))
        return True
    except OSError:
        pass
    return False


def is_connected_http(host="http://duckduckgo.com"):
    try:
        status = requests.head(host).status_code
        return True
    except OSError:
        pass
    return False


def is_connected():
    return any((is_connected_dns(), is_connected_http()))
