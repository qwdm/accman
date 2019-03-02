#!/bin/bash
docker run -d \
    --name accman_postgres \
    -v my_dbdata:/var/lib/postgresql/data \
    -p 54320:5432 \
    accman_postgres:latest
