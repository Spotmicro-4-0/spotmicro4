#!/bin/bash

# String constants
USAGE_MSG="Usage: $0 {on|off}"
ENABLE_ON_LABEL="on  - Enable SpotmicroAI to run on boot"
DISABLE_OFF_LABEL="off - Disable SpotmicroAI from running on boot"
ENABLING_MSG="Enabling SpotmicroAI to run on boot"
DISABLING_MSG="Disabling SpotmicroAI from running on boot"
DONE_MSG="Done"
NOT_RUNNING_MSG="Service spotmicroai is not running, run 'sudo systemctl start spotmicroai.service' to start it"
NOT_INSTALLED_MSG="Service spotmicroai is not installed as service"
STILL_RUNNING_MSG="Service spotmicroai is still running, run 'sudo systemctl stop spotmicroai.service' to stop it"
INVALID_OPTION_MSG="Error: Invalid option"

service_exists() {
    local n=$1
    if [[ $(systemctl list-units --all -t service --full --no-legend "$n.service" | cut -f1 -d' ') == $n.service ]]; then
        return 0
    else
        return 1
    fi
}

show_usage() {
    echo "$USAGE_MSG"
    echo "  $ENABLE_ON_LABEL"
    echo "  $DISABLE_OFF_LABEL"
    exit 1
}

if [[ $# -ne 1 ]]; then
    show_usage
fi

case "$1" in
    on)
        echo "$ENABLING_MSG"
        yes | sudo cp -f ~/spotmicroai/utilities/boot/spotmicroai.service /etc/systemd/system/spotmicroai.service
        sudo systemctl enable spotmicroai.service
        sudo systemctl daemon-reload
        echo "$DONE_MSG"
        if ! systemctl is-active --quiet spotmicroai; then
            echo "$NOT_RUNNING_MSG"
        fi
        ;;
    off)
        if ! service_exists spotmicroai; then
            echo "$NOT_INSTALLED_MSG"
            exit 1
        fi
        echo "$DISABLING_MSG"
        sudo systemctl disable spotmicroai.service
        sudo systemctl daemon-reload
        echo "$DONE_MSG"
        if systemctl is-active --quiet spotmicroai; then
            echo "$STILL_RUNNING_MSG"
        fi
        ;;
    *)
        echo "$INVALID_OPTION_MSG '$1'"
        show_usage
        ;;
esac

