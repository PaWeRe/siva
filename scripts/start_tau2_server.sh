#!/bin/bash

echo "Starting the Siva server..."
uvicorn src.sive.api_service.simulation_service:app --host 127.0.0.1 --port 8001