#!/usr/bin/env bash

function launch-process() {
    name-to-script-path ${1}

    # Launch process in foreground
    echo "Starting $1"
    python3 -m ${_module} $_params
}

function require-process() {
    # Launch process if not found
    name-to-script-path ${1}
    if ! pgrep -f "python3 -m ${_module}" > /dev/null ; then
        # Start required process
        launch-background ${1}
    fi
}

function launch-background() {
    # Check if given module is running and start (or restart if running)
    name-to-script-path ${1}
    if pgrep -f "python3 -m ${_module}" > /dev/null ; then
        if ($_force_restart) ; then
            echo "Restarting: ${1}"
            "${DIR}/stop-mycroft.sh" ${1}
        else
            # Already running, no need to restart
            return
        fi
    else
        echo "Starting background service $1"
    fi

    # Security warning/reminder for the user
    if [[ "${1}" == "bus" ]] ; then
        echo "CAUTION: The Mycroft bus is an open websocket with no built-in security"
        echo "         measures.  You are responsible for protecting the local port"
        echo "         8181 with a firewall as appropriate."
    fi

    # Launch process in background, sending logs to standard location
    python3 -m ${_module} $_params >> /var/log/mycroft/${1}.log 2>&1 &
}
