#!/bin/bash

# Create docker images for bash, sql environments
# echo "Setting up docker image for bash..."
# docker build -t intercode-bash -f docker/bash.Dockerfile .

# echo "Setting up docker image for nl2bash..."
docker build -t intercode-nl2bash-fs-1 -f docker/nl2bash_fs_1.Dockerfile .

# echo "Setting up docker image for nl2bash..."
docker build -t intercode-nl2bash-fs-2 -f docker/nl2bash_fs_2.Dockerfile .

# echo "Setting up docker image for nl2bash..."
docker build -t intercode-nl2bash-fs-3 -f docker/nl2bash_fs_3.Dockerfile .

# echo "Setting up docker image for nl2bash..."
docker build -t intercode-nl2bash-fs-4 -f docker/nl2bash_fs_4.Dockerfile .

# echo "Setting up docker image for sql..."
docker compose -f docker/sql-docker-compose.yml up -d





