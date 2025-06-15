#!/bin/bash
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -U "solar_user" -d "solar_platform"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Execute the main command
exec $cmd