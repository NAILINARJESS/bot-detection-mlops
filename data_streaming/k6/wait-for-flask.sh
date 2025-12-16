#!/bin/sh

set -e

hostport="$1"
shift
cmd="$@"

echo "Waiting for Flask at $hostport ..."

until curl -s http://$hostport/bot_event > /dev/null; do
  echo "Flask unavailable - sleeping"
  sleep 2
done

echo "Flask is up - executing command"

exec $cmd

