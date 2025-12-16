#!/bin/sh

set -e

host_port="$1"
shift

echo "Waiting for Kafka at $host_port..."

until nc -z $(echo $host_port | cut -d':' -f1) $(echo $host_port | cut -d':' -f2); do
  echo "Kafka unavailable - sleeping"
  sleep 2
done

echo "Kafka is up - executing command"

exec "$@"

