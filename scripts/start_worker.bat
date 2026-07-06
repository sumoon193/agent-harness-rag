@echo off
REM 启动 Celery 文档入库 worker（Windows 版）。
REM 用法: scripts\start_worker.bat [concurrency]

set CONCURRENCY=%1
if "%CONCURRENCY%"=="" set CONCURRENCY=2

echo === EnterpriseMind Celery Worker ===
echo Concurrency: %CONCURRENCY%
echo.

celery -A app.services.ingestion.celery_app.celery_app worker --loglevel=info --concurrency=%CONCURRENCY% --pool=solo -Q default
