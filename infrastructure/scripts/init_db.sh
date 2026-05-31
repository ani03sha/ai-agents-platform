#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL="${SCRIPT_DIR}/../db/001_init.sql"

echo "Waiting for Postgres..."
until docker exec agents-postgres pg_isready -U agents -d agents > /dev/null 2>&1; do sleep 2; done

echo "Applying schema..."
docker exec -i agents-postgres psql -U agents -d agents < "${SQL}"

echo "Tables:"
docker exec agents-postgres psql -U agents -d agents -c "\dt"