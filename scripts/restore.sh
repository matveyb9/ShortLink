#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_file.sql.gz>"
    exit 1
fi

source .env
BACKUP_FILE=$1

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will overwrite the current database!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Starting restore from ${BACKUP_FILE}"

# Распаковка
gunzip -c ${BACKUP_FILE} | docker exec -i urlshortener_postgres psql -U ${DB_USER} ${DB_NAME}

if [ $? -eq 0 ]; then
    echo "Restore completed successfully"
else
    echo "Restore failed!"
    exit 1
fi