#!/bin/bash

# Конфигурация
source .env
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Создание директории для бэкапов
mkdir -p ${BACKUP_DIR}

echo "Starting backup at $(date)"

# Создание бэкапа
docker exec urlshortener_postgres pg_dump -U ${DB_USER} ${DB_NAME} > ${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "Backup created successfully: ${BACKUP_FILE}"
    
    # Сжатие
    gzip ${BACKUP_FILE}
    echo "Backup compressed: ${BACKUP_FILE}.gz"
    
    # Удаление старых бэкапов
    find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    echo "Old backups cleaned (older than ${RETENTION_DAYS} days)"
else
    echo "Backup failed!"
    exit 1
fi

echo "Backup completed at $(date)"