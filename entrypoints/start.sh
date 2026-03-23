#!/bin/bash
set -e

echo "Waiting for MongoDB..."
until nc -z file_mongo 27017; do
  sleep 1
done

echo "Waiting for MinIO..."
until nc -z file_minio 9000; do
  sleep 1
done

echo "Starting File FastAPI server..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8020
