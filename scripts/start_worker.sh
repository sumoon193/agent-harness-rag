#!/usr/bin/env bash
# 启动 Celery 文档入库 worker。
# 用法: ./scripts/start_worker.sh [concurrency]
# 默认 concurrency=2。

set -euo pipefail

CONCURRENCY="${1:-2}"

echo "=== EnterpriseMind Celery Worker ==="
echo "Broker: ${CELERY_BROKER_URL:-$REDIS_URL}"
echo "Concurrency: $CONCURRENCY"
echo ""

celery -A app.services.ingestion.celery_app.celery_app worker \
  --loglevel=info \
  --concurrency="$CONCURRENCY" \
  --pool=prefork \
  -Q default \
  -n ingestion-worker@%h
