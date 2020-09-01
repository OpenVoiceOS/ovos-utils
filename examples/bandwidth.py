import time
import glob
import re
import os
import curses
import socket

refresh = 5


def load():
    with open("/proc/net/tcp", "r") as f:
        content = f.readlines()
        content.pop(0)  # get rid of the header
    return content


def ip(octet):
    return str(int(octet[6:8], 16)) + "." + str(
        int(octet[4:6], 16)) + "." + str(int(octet[2:4], 16)) + "." + str(
        int(octet[:2], 16))


def port(port):
    return str(int(port[:2], 16)) + str(int(port[2:4], 16))


def get_pid(inode):
    for i in glob.glob("/proc/[0-9]*/fd/[0-9]*"):
        try:
            if re.search(inode, os.readlink(i)):
                return i.split("/")[2]
        except:
            pass
    return None


def get_host(ip):
    try:
        data = socket.gethostbyaddr(ip)
        host = repr(data[0])
        return host
    except Exception:
        return ip


def _draw_ip(conn):
    message = 80 * "~" + "\nLocal\t\t\tRemote\t\t\tProgram\n" + \
              80 * "~" + "\n"
    for ipp in conn:
        localip = ip(ipp.split("-")[0].split(":")[0])
        remoteip = ip(ipp.split("-")[1].split(":")[0])
        localport = port(ipp.split("-")[0].split(":")[1])
        remoteport = port(ipp.split("-")[1].split(":")[1])

        if remoteport.startswith("0"):
            remoteport = remoteport[1:]

        inode = ipp.split("-")[2]
        pid = get_pid(inode)
        try:
            exe = os.readlink("/proc/" + pid + "/exe")
        except:
            exe = "Remote"

        if len(localip + localport) < 15:
            message += localip + ":" + localport + "\t\t"
        else:
            message += localip + ":" + localport + "\t"

        if len(remoteip + remoteport) < 15:
            message += remoteip + ":" + remoteport + "\t\t" + exe + "\n"
        else:
            message += remoteip + ":" + remoteport + "\t" + exe + "\n"
    return message


def _draw_host(conn):
    message = 80 * "~" + "\nProgram\t\t\tDevice\t\t\t\tRemote Hostname\n" + \
              80 * "~" + "\n"
    cons = []
    for ipp in conn:
        localip = ip(ipp.split("-")[0].split(":")[0])
        remoteip = ip(ipp.split("-")[1].split(":")[0])
        inode = ipp.split("-")[2]
        pid = get_pid(inode)
        try:
            exe = os.readlink("/proc/" + pid + "/exe").split("/")[-1]
        except:
            continue

        localhost = get_host(localip)
        remotehost = get_host(remoteip)
        data_point = (exe, localhost, remotehost)
        if data_point not in cons:
            cons += [data_point]

    for exe, localhost, remotehost in cons:
        if len(exe) < 15:
            message += exe + "\t\t\t" + localhost + "\t" + remotehost + "\n"
        else:
            message += exe + "\t" + localhost + "\t" + remotehost + "\n"
    return message


def start():
    window = curses.initscr()
    curses.noecho()
    curses.cbreak()
    window.keypad(1)
    curses.curs_set(0)

    while True:
        title = "Established TCP connections on the system\n"
        conn = []
        tcp = load()
        for line in tcp:
            d_line = line.split()
            if d_line[3] == "01":
                conn.append(d_line[1] + "-" + d_line[2] + "-" + d_line[9])

        message = _draw_ip(conn)

        try:
            window.addstr(0, 0, title + message)
        except:
            pass
        window.clrtobot()
        window.refresh()
        time.sleep(refresh)


if __name__ == "__main__":
    start()
