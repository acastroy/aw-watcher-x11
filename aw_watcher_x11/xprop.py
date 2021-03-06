import sys
import subprocess
from subprocess import PIPE
import re
import logging

logger = logging.getLogger("aw_watcher_x11.xprop")

# req_version is 3.5 due to usage of subprocess.run
# It would be nice to be able to use 3.4 as well since it's still common as of May 2016
req_version = (3, 5)
cur_version = sys.version_info

if not cur_version >= req_version:
    logger.error("Your Python version is too old, 3.5 or higher is required.")
    exit(1)


def xprop_id(window_id) -> str:
    cmd = ["xprop"]
    cmd.append("-id")
    cmd.append(window_id)
    p = subprocess.run(cmd, stdout=PIPE)
    return str(p.stdout, "utf8")


def xprop_root() -> str:
    cmd = ["xprop"]
    cmd.append("-root")
    p = subprocess.run(cmd, stdout=PIPE)
    return str(p.stdout, "utf8")


def get_active_window_id():
    lines = xprop_root().split("\n")
    client_list = next(filter(lambda x: "_NET_ACTIVE_WINDOW(" in x, lines))
    wid = re.findall("0x[0-9a-f]*", client_list)[0]
    return wid


def get_window_ids():
    lines = xprop_root().split("\n")
    client_list = next(filter(lambda x: "_NET_CLIENT_LIST(" in x, lines))
    window_ids = re.findall("0x[0-9a-f]*", client_list)
    return window_ids


def _extract_xprop_field(line):
    return "".join(line.split("=")[1:]).strip(" \n")


def get_xprop_field(fieldname, xprop_output):
    return list(map(_extract_xprop_field, re.findall(fieldname + ".*\n", xprop_output)))


def get_xprop_field_str(fieldname, xprop_output) -> str:
    return get_xprop_field(fieldname, xprop_output)[0].strip('"')


def get_xprop_field_strlist(fieldname, xprop_output) -> str:
    return [s.strip('"') for s in get_xprop_field(fieldname, xprop_output)]


def get_xprop_field_class(xprop_output) -> str:
    return [c.strip('", ') for c in get_xprop_field("WM_CLASS", xprop_output)[0].split(',')]


def get_xprop_field_int(fieldname, xprop_output) -> int:
    return int(get_xprop_field(fieldname, xprop_output)[0])


def get_window(wid, active_window=False):
    s = xprop_id(wid)
    window = {
        "id": wid,
        "active": active_window,
        "name": get_xprop_field_str("WM_NAME", s),
        "class": get_xprop_field_class(s),
        "desktop": get_xprop_field_int("WM_DESKTOP", s),
        "command": get_xprop_field("WM_COMMAND", s),
        "role": get_xprop_field_strlist("WM_WINDOW_ROLE", s),
        "pid": get_xprop_field_int("WM_PID", s),
    }

    return window


def get_windows(wids, active_window_id=None):
    return [get_window(wid, active_window=(wid == active_window_id)) for wid in wids]
