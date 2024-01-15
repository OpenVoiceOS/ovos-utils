import re
import os
from datetime import datetime
from traceback import FrameSummary
from dataclasses import dataclass
from typing import Any, Tuple, List, Generator, Dict, Union, Optional

from dateutil.parser import parse
import rich_click as click
from rich.console import Console
from rich.style import Style
from rich.table import Table
import pydoc
from combo_lock import ComboLock

try:
    from ovos_config import Configuration
    use24h = Configuration().get("time_format", "full") == "full"
    date_format = Configuration().get("date_format", "DMY")
except ImportError:
    use24h = True
    date_format = "DMY"
    
from ovos_utils.log import get_log_path, get_log_paths, get_available_logs


TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
LOGLOCK = ComboLock("ovos_logs_console_script")


@dataclass
class LogLine:
    timestamp: datetime = None
    source: str = ""
    location: str = ""
    level: str = ""
    message: str = ""

    def __str__(self):
        # sytsem messages etc.
        if not all([self.source, self.location, self.level]):
            return self.message
        return f"{self.format_timestamp()} - {self.source} - {self.location} - {self.level} - {self.message}"
    
    def format_timestamp(self):
        if self.timestamp:
            return self.timestamp.strftime(TIME_FORMAT)[:-3]
        return ""


# Traceback frame
class Frame(FrameSummary):
    def __init__(self, filename, lineno, name, line):
        super().__init__(filename, lineno, name, line=line)
      
    def as_dict(self):
        return {
            "location": self.format_location(),
            "level": "TRACEBACK",
            "message": self.line
        }
    
    def as_logline(self):
        return LogLine(**self.as_dict())
    
    def format_location(self):
        if "/bin/" in self.filename:
            package = self.filename.split("/bin/")[-1].replace(".py", "")\
                    .replace("-", "_").replace("/", ".")
        elif "site-packages" not in self.filename and \
                (pyver := re.search(r"python\d\.\d+[\\/]", self.filename)):
            package = self.filename.split(pyver.group())[-1].replace(".py", "")\
                    .replace("-", "_").replace("/", ".")
        else:
            package = self.filename.split("site-packages/")[-1].replace(".py", "")\
                    .replace("-", "_").replace("/", ".")
        method = self.name.replace(".py", "").replace("-", "_")
        return f"{package}:{method}:{self.lineno}"
    
    def __str__(self):
        return f'  File "{self.filename}", line {self.lineno}, in {self.name}\n    {self.line}\n'


class Traceback:
    PATTERN = r'File "(?P<filename>[^"]+)", line (?P<lineno>\d+), in (?P<name>\S+)\n\s*(?P<line>.+)'

    def __init__(self, frames: List[Frame], exception: str, timestamp: datetime = None):
        self.frames = frames
        self.exception = exception
        self._timestamp = timestamp
    
    @property
    def exception_location(self):
        return self.frames[-1].format_location()
    
    @property
    def timestamp(self):
        return self._timestamp
    
    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = value

    def to_loglines(self) -> List[LogLine]:
        
        lines = [LogLine(timestamp=self.timestamp,
                         location=self.exception_location,
                         level="EXCEPTION",
                         message=self.exception)]

        for frame in self.frames:
            lines.append(frame.as_logline())
        
        return lines

    @classmethod
    def from_list(cls, lines):
        lines = [line if line.endswith("\n") else line + "\n" for line in lines]
        multiline = "".join(lines)
        return cls.from_string(multiline)
    
    @classmethod
    def from_string(cls, s):
        matches = re.findall(cls.PATTERN, s, re.MULTILINE)
        frames = []
        for match in matches:
            data = dict(zip(["filename", "lineno", "name", "line"], match))
            frames.append(Frame(**data))
        exception = next(line for line in s.split("\n")[::-1] if line)
        return cls(frames, exception)
    
    def __str__(self):
        multiline = "Traceback (most recent call last):\n"
        for frame in self.frames:
            multiline += str(frame)
        multiline += f"{self.exception}\n"
        return multiline


class OVOSLogParser:
    LOG_PATTERN = r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{1,6}) - (?P<source>.+?) - (?P<location>.+?) - (?P<level>\w+) - (?P<message>.*)'

    @classmethod
    def parse(self, log_line, last_timestamp=None) -> LogLine:
        log_line.rstrip("\n")
        match = re.match(self.LOG_PATTERN, log_line)
        data = {}
        if match:
            data = match.groupdict()
            data['timestamp'] = datetime.strptime(data['timestamp'], TIME_FORMAT)
            return LogLine(**data)
        
        data["timestamp"] = last_timestamp or ""
        data["message"] = log_line
        return LogLine(**data)
    
    @classmethod
    def parse_file(self, source) -> Generator[Union[LogLine, Traceback], None, None]:
        if not os.path.exists(source):
            raise FileNotFoundError(f"File {source} does not exist")

        with open(source, 'r') as file:
            trace = None
            last_timestamp = None
            for line in file:
                # gather all lines of the traceback
                if line == "Traceback (most recent call last):\n":
                    trace = [line]
                    continue
                # TODO do tracebacks always end on a empty line?
                elif trace and line == "\n":
                    trace.append(line)
                    traceback = Traceback.from_list(trace)
                    traceback.timestamp = last_timestamp
                    yield traceback
                    trace = None
                elif trace:
                    trace.append(line)
                else:
                    log = self.parse(line, last_timestamp)
                    if log.message == "\n":
                        continue
                    timestamp = log.timestamp
                    if timestamp:
                        last_timestamp = timestamp
                    yield log


console = Console()

EXPECTED_DATE_FORMAT = "YYYY-MM-DD" if date_format == "YMD" else "DD-MM-YYYY"
EXPECTED_DATE = "2023-12-01" if date_format == "YMD" else "01-12-2023"
EXPECTED_DATETIME_FORMAT = f'"[{EXPECTED_DATE_FORMAT}] HH:MM[:SS]{" AM/PM" if not use24h else ""}"'
EXPECTED_TIME = f'"09:00:05{" PM" if not use24h else ""}"'

LOGSOPTHELP = """logs to be sliced 
\n\nmultiple: -l bus -l audio"""
STARTTIMEHELP = f"""start time of the log slice (default: since service restart,
input format: {EXPECTED_DATETIME_FORMAT})
\n\nExample: -s \"{EXPECTED_DATE} 12:00{' AM/PM' if not use24h else ''}\" / -s
 {'"' if not use24h else ''}12:00:05{' AM/PM"' if not use24h else ''}"""

click.rich_click.STYLE_ARGUMENT = "dark_red"
click.rich_click.STYLE_OPTION = "dark_red"
click.rich_click.STYLE_SWITCH = "indian_red"
click.rich_click.USE_MARKDOWN = True
click.rich_click.COMMAND_GROUPS = {
    "ovos-logs": [
        {
            "name": "Slice logs by time",
            "commands": ["slice"],
            "table_styles": {
                "row_styles": ["white"],
                "padding": (0, 2),
                "title_justify": "left"
            },
        },
        {
            "name": "List logs by severity",
            "commands": ["list"],
            "table_styles": {
                "row_styles": ["white"],
                "padding": (0, 2),
            },
        },
        {
            "name": "Downsize logs",
            "commands": ["reduce"],
            "table_styles": {
                "row_styles": ["white"],
                "padding": (0, 1),
            },
        },
        {
            "name": "Show logs (using less)",
            "commands": ["show"],
            "table_styles": {
                "row_styles": ["white"],
                "padding": (0, 2),
            },
        }
    ]
}


def get_last_load_time(directories: Optional[List[str]] = None) -> Optional[datetime]:
    # if nothing's found return the beginning of unix time
    last_timestamp = datetime.fromtimestamp(0)
    if directories is None:
        directory = get_log_path("skills")
    else:
        directory = get_log_path("skills", directories)
    
    if directory:
        with open(os.path.join(directory,"skills.log"), "r") as f:
            for line in f.readlines()[::-1]:
                logline = OVOSLogParser.parse(line)
                if logline.timestamp:
                    last_timestamp = logline.timestamp 
                if logline.message == "Loading message bus configs":
                    break
    return last_timestamp


def valid_log(logs, paths):
    for log in logs:
        if log.lower() not in get_available_logs(paths):
            return False
    return True


def parse_time(time_str):
    try:
        time = parse(time_str)
    except ValueError:
        return None
    return time


def get_timestamped_filename(basename: str, ext: str, basedir = "~", timeformat = '%Y%m%d_%H%M%S'):
    if basedir == "~":
        basedir = os.path.expanduser("~")

    t = datetime.now().strftime(timeformat)
    return os.path.join(basedir, f"{basename}_{t}.{ext}")


def parse_timeframe(start, end, directories: Optional[List[str]] = None) -> Tuple[Any, Any]:
    """
    Parses the start and end time given a string input.
    If the start is None, parse the skill log to determine the last service load time and
    if that fails return the beginning starting datetime of the log.
    If the end is None, return the current datetime. 

    :param start: start time of the log slice (default: since service restart)
    :param end: end time of the log slice (default: now)
    :param directories: the directory logs reside in
    :return: start and end time
    """
    if start is None:
        start = get_last_load_time(directories)
    else:
        start = parse_time(start)
    
    if end is None:
        end = datetime.now()
    else:
        end = parse_time(end)
    return start, end


@click.group()
def ovos_logs():
    """\b
    Small helper tool to quickly navigate the logs, create slices and quickview errors

    `ovos-logs [COMMAND] --help` for further information about the specific command ARGUMENTS
    \b
    """
    pass


@ovos_logs.command()
@click.option("--start", "-s", help=STARTTIMEHELP)
@click.option("--until", "-u", help=f"end time of the log slice [default: now]")
@click.option("--logs", "-l", multiple=True, default=get_available_logs(), help=LOGSOPTHELP, show_default=True)
@click.option("--paths", "-p", multiple=True, default=get_log_paths(), help=f"the directory logs reside in", show_default=True)
@click.option("--file", "-f", is_flag=False, flag_value=get_timestamped_filename("slice", "log"),
              default=None, help=f"output as file (if flagged, but not specified: {get_timestamped_filename('slice', 'log')})")
def slice(start, until, logs, paths, file):
    """\b
    Optionally define start (`-s`) and the time until (`-u`) the slice should be limited to.  
    \b
    Different logs can be included using the `-l` option. If not specified, all logs will be included.  
    Optionally the directory where the logs are stored (`-p`) and the file where the slices should be dumped (`-f`)
    can be specified.  
    \b
    > Examples:  
    > ovos-logs slice                                            # Slice all logs from service start up until now  
    > ovos-logs slice -s 01-12-2023 -u '01-12-2023 17:00:20'     # Slice all logs from the start of december the first until 17:00:20  
    > ovos-logs slice -l bus -l skills -f ~/myslice.log          # Slice skills.log and bus.log from service start up until now and dump it to the file ~/myslice.log  
    """
    logs_present = []

    if not all(os.path.exists(path) for path in paths):
        return console.print(f"Directory [{[p for p in paths if not os.path.exists(p)]}] does not exist")
    else:
        logs_present = get_available_logs(paths)

    start, end = parse_timeframe(start, until, paths)
    if start is None:
        return console.print(f"Need a valid start time in the format {EXPECTED_DATETIME_FORMAT}")
    elif end is None:
        return console.print(f"Need a valid end time in the format {EXPECTED_DATETIME_FORMAT}")
    elif start > end:
        return console.print(f"Start time [{start}] is after end time [{end}]")

    if not logs:
        logs = logs_present
    elif not valid_log(logs, paths):
        return console.print(f"Invalid log name, valid logs are {logs_present}")

    _templog: Dict[str, List[LogLine]] = dict()

    for service in logs:
        path = get_log_path(service, paths)
        logfile = os.path.join(path, f"{service}.log")
        if not os.path.exists(logfile):
            continue
        _templog[service] = []
        for log in OVOSLogParser.parse_file(logfile):
            if start <= log.timestamp < end:
                if isinstance(log, Traceback):
                    _templog[service].extend(log.to_loglines())
                else:
                    _templog[service].append(log)
        if not _templog[service]:
            del _templog[service]

    if not _templog:
        return console.print("No logs found in the specified time frame")
    
    if file is not None:
        # test if file is writable
        try:
            with open(file, 'w') as f:
                pass
        except:
            return console.print(f"File [{file}] is not writable. Aborted")
        else:
            console.print(f"Log slice saved to [bold]{file}[/bold]")

    for service in _templog:
        table = Table(title=service)
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column()
        table.add_column("Message", style="magenta")
        table.add_column("Origin", style="green")
        lineno = 0
        for logline in _templog[service]:
            lineno += 1
            style = None
            timestamp = logline.timestamp or ""
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%H:%M:%S.%f" if use24h else "%I:%M:%S.%f")[:-3]
                if not use24h:
                    timestamp += logline.timestamp.strftime(" %p")

            level = logline.level or ""
            message = logline.message or ""
            if level == "ERROR":
                level = "[bold red]" + level[:1]
            elif level == "EXCEPTION":
                level = "[bold red]" + level[:3]
            elif level == "WARNING":
                level = "[bold yellow]" + level[:1]
            elif level == "DEBUG":
                level = "[bold blue]" + level[:1]
            elif level == "TRACEBACK":
                level = "[white]" + level[:5]
                message = "[grey42]" + message
            elif level == "INFO":
                level = ""
                message = "[navajo_white1]" + message
            if lineno % 2 == 0:
                style = Style(bgcolor="grey7")
            table.add_row(
                timestamp,
                level,
                message,
                logline.location or "",
                style=style
            )
            if len(logline.message) > 200:
                table.add_row()

        console.print(table)
        if file:
            Console(file=open(file, 'a')).print(table)


@ovos_logs.command()
@click.option("--error", "-e", is_flag=True, help="display error messages")
@click.option("--warning", "-w", is_flag=True, help="display warning messages")
@click.option("--exception", "-x", is_flag=True, help="display exceptions")
@click.option("--debug", "-d", is_flag=True, help="display debug messages")
@click.option("--start", "-s", help=STARTTIMEHELP)
@click.option("--until", "-u", help=f"end time of the log slice [default: now]")
@click.option("--logs", "-l", multiple=True, default=get_available_logs(), help=LOGSOPTHELP, show_default=True)
@click.option("--paths", "-p", multiple=True, type=click.Path(), default=get_log_paths(), help=f"the directory logs reside in", show_default=True)
@click.option("--file", "-f", is_flag=False, type=click.Path(), flag_value=get_timestamped_filename("list", "log"), default=None,
              help=f"output as file (if flagged, but not specified: {get_timestamped_filename('list', 'log')})")
def list(error, warning, exception, debug, start, until, logs, paths, file):
    """\b
    Log level has to be specified.  
    \b
    Optionally define start (`-s`) and the time until (`-u`) the slice should be limited to.  
    \b
    Different logs can be included using the `-l` option. If not specified, all logs will be included.  
    \b
    Optionally the directory where the logs are stored (`-p`) and the file where the slices should be dumped (`-f`)
    can be specified.  
    \b
    > Examples:  
    > ovos-logs list -x                                           # List all exceptions from service start up until now  
    > ovos-logs list -e -w -s 01-12-2023 -u '01-12-2023 17:00:20' # List all errors and warnings from the start of december the first until 17:00:20  
    > ovos-logs list -x -l bus -l skills -f                       # List all exceptions from skills.log and bus.log and dump it to the file ~/list_xxx_xxx.log  
    """
    if not any([error, warning, debug, exception]):
        return console.print("Need at least one of --error, --warning, --exception or --debug")
    else:
        log_levels = [lv_str for lv, lv_str in [(error, "ERROR"), (warning, "WARNING"),
                                                (debug, "DEBUG"), (exception, "EXCEPTION")] if lv]

    if not all(os.path.exists(path) for path in paths):
        return console.print(f"Directory [{[p for p in paths if not os.path.exists(p)]}] does not exist")
    else:
        logs_present = get_available_logs(paths)

    start, end = parse_timeframe(start, until, paths)
    if start is None:
        return console.print(f"Need a valid start time in the format {EXPECTED_DATETIME_FORMAT}")
    elif end is None:
        return console.print(f"Need a valid end time in the format {EXPECTED_DATETIME_FORMAT}")
    elif start > end:
        return console.print(f"Start time [{start}] is after end time [{end}]")
    
    if not logs:
        logs = logs_present
    elif not valid_log(logs, paths):
        return console.print(f"Invalid log name, valid logs are {logs_present}")
    
    _templog: Dict[str, List[LogLine]] = dict()

    for service in logs:
        path = get_log_path(service, paths)
        if path is None:
            continue
        logfile = os.path.join(path, f"{service}.log")
        _templog[service] = []
        for log in OVOSLogParser.parse_file(logfile):
            if isinstance(log, Traceback):
                if exception:
                    _templog[service].extend(log.to_loglines())
                continue
            # LOG.exception
            if exception and log.level == "EXCEPTION":
                _templog[service].append(log)
            if error and log.level == "ERROR":
                _templog[service].append(log)
            if warning and log.level == "WARNING":
                _templog[service].append(log)
            if debug and log.level == "DEBUG":
                _templog[service].append(log)
        if not _templog[service]:
            del _templog[service]
    
    if not _templog:
        return console.print("No logs found for the specified log level")
    
    if file is not None:
        # test if file is writable
        try:
            with open(file, 'w') as f:
                pass
        except:
            return console.print(f"File [{file}] is not writable. Aborted")
        else:
            console.print(f"Log list saved to [bold]{file}[/bold]")

    for service in _templog:
        table = Table(title=f"{service} ({','.join(log_levels)})")
        # for traceback indication
        table.add_column("Time", style="cyan", no_wrap=True)
        if exception or len(log_levels) > 1:
            table.add_column()
        table.add_column("Message", style="magenta")
        table.add_column("Origin", style="green")
        lineno = 0
        for log in _templog[service]:
            style = None
            lineno += 1
            timestamp = log.timestamp or ""
            if timestamp:
                timestamp = timestamp.strftime("%H:%M:%S.%f" if use24h else "%I:%M:%S.%f")[:-3]
            if not use24h and timestamp:
                timestamp += log.timestamp.strftime(" %p")
            level = log.level.upper()
            message = log.message.rstrip("\n")
            if level == "ERROR":
                level = "[bold red]" + level[:1]
            elif level == "EXCEPTION":
                level = "[bold red]" + level[:3]
            elif level == "WARNING":
                level = "[bold yellow]" + level[:1]
            elif level == "DEBUG":
                level = "[bold blue]" + level[:1]
            elif level == "TRACEBACK":
                level = "[white]" + level[:5]
                message = "[grey42]" + message
            elif level == "INFO":
                level = ""
                message = "[navajo_white1]" + message

            if lineno % 2 == 0:
                style = Style(bgcolor="grey7")
            row = [timestamp, level, message, log.location]
            if not exception and len(log_levels) < 2:
                row.pop(1)                
            table.add_row(*row, style=style)
            if len(log.message) > 200:
                table.add_row()

        console.print(table)
        if file:
            Console(file=open(file, 'a')).print(table)

    
@ovos_logs.command()
@click.option("--log", "-l", required=True, type=click.Choice(get_available_logs(), case_sensitive=False), help=f"log to show; available: {get_available_logs()}")
@click.option("--paths", "-p", multiple=True, type=click.Path(), default=get_log_paths(), help=f"the directory logs reside in", show_default=True)
def show(log, paths):
    """\b
    A service log has to be specified (`-l`).  
    \b
    Optionally the directory where the logs are stored (`-p`) can be specified.  
    \b
    > Examples:  
    > ovos-logs show -l skills                                    # Display skills.log   
    > ovos-logs show -l debug -p ~/custom_path/                   # Display debug.log from a custom path     
    """
    if not any(os.path.exists(os.path.join(path, f"{log}.log")) for path in paths):
        return console.print(f"File does not exist")
    else:
        log = os.path.join(get_log_path(log, paths), f"{log}.log")
    
    pydoc.pager(open(log).read())


@ovos_logs.command()
@click.option("--size", "-s", is_flag=False, flag_value=None, default=0, help="truncate logs to a given size (in bytes)")
@click.option("--date", "-d", help="truncate logs to a given date")
@click.option("--logs", "-l", multiple=True, default=get_available_logs(), help=LOGSOPTHELP, show_default=True)
@click.option("--paths", "-p", multiple=True, type=click.Path(), default=get_log_paths(), help=f"the directory logs reside in", show_default=True)
def reduce(size, date, logs, paths):
    """\b
    Reduce logs to a given size (in bytes) or remove entries before a given date.  
    \b
    Different logs can be included using the `-l` option. If not specified, all logs will be included.  
    Optionally the directory where the logs are stored (`-p`) can be specified.  
    \b
    > Examples:  
    > ovos-logs reduce                                            # Reduce all logs to 0 bytes  
    > ovos-logs reduce -s 1000000                                 # Reduce all logs to ~1MB (latest logs)  
    > ovos-logs reduce -d "1-12-2023 17:00"                       # Reduce all logs to entries after the specified date/time  
    > ovos-logs reduce -s 1000000 -l skills -l bus                # Reduce skills.log and bus.log to ~1MB (latest logs)  
    """

    if date:
        size = None
        date = parse_time(date)
        if date is None:
            return console.print(f"The date/time provided couldn't be parsed. Expected format: {EXPECTED_DATETIME_FORMAT}")
        
    if not all(os.path.exists(path) for path in paths):
        return console.print(f"Directory [{[p for p in paths if not os.path.exists(p)]}] does not exist")
    else:
        logs_present = get_available_logs(paths)
    
    if not logs:
        logs = logs_present
    elif not valid_log(logs, paths):
        return console.print(f"Invalid log name, valid logs are {logs_present}")
    
    for service in logs:
        path = get_log_path(service, paths)
        logfile = os.path.join(path, f"{service}.log")
        reduced = False
        with LOGLOCK:
            if size:
                with open(logfile, 'r') as f:
                    f.seek(0, os.SEEK_END)
                    fullsize = f.tell()
                    f.seek(max(fullsize - size, 0))
                    # skip cutoff line
                    f.readline()
                    remaining_lines = f.readlines()
                if fullsize > size and remaining_lines:
                    reduced = True
                    with open(logfile, 'w') as f:
                        f.writelines(remaining_lines)
            elif date:
                loglines = []
                for log in OVOSLogParser.parse_file(logfile):
                    if log.timestamp and log.timestamp < date:
                        reduced = True
                        continue
                    loglines.append(log)
                if reduced:
                    with open(logfile, 'w') as f:
                        for log in loglines:
                            f.write(str(log) + "\n")
            else:
                reduced = True
                with open(logfile, 'w') as f:
                    f.write("")

        if reduced:
            console.print(f"{service} log reduced")
