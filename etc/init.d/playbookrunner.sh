#!/bin/sh

### BEGIN INIT INFO
# Provides:          playbookrunner
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Harden and domain join Linux servers 
# Description:       Service to monitor ansible inventory file for new servers whose names match a specified pattern and execute ansible playbook against new Linux servers to harden and join them to domain.
### END INIT INFO

# http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/
# https://www.wyre-it.co.uk/blog/converting-from-sysvinit-to-systemd/

set -x

# Change the next 3 lines to suit where you install your script and what you want to call it
#DIR=/usr/local/bin/playbookrunner
DIR=/home/rob/dev/git/pymultiprocess
DAEMON=$DIR/playbookrunner.py
DAEMON_NAME=playbookrunner
LOG_DIR=/var/log/playbookrunner
LOG_FILENAME=$LOG_DIR/${DAEMON_NAME}.log

# Add any command line options for your daemon here
DAEMON_OPTS="--log $LOG_FILENAME"

# This next line determines what user the script runs as.
# Root generally not recommended but necessary if you are using the Raspberry Pi GPIO from Python.
DAEMON_USER=rob

UMASK=0022
mkdir -p $LOG_DIR
touch $LOG_FILENAME
chown $DAEMON_USER:$DAEMON_USER $LOG_FILENAME

# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting system $DAEMON_NAME daemon"
    start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --signal INT --pidfile $PIDFILE --retry 10
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0
