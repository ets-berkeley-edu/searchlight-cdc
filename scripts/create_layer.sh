#!/usr/bin/env bash

set -e

function usage() {
    echo
    echo "    Usage: $0 layer_name packages"
    echo
    echo "    e.g.   $0 boto3-python313 boto3"
    echo
    exit
}
if [ $# -ne 2 ]; then
    usage
fi

LAYER_NAME=$1
PACKAGES=$2

# Set the directory where the Dockerfile is located
DIRECTORY="$(pwd)"

# Build the Docker image
docker build -t lambda-layer --build-arg PACKAGES=$PACKAGES --build-arg LAYER_NAME=$LAYER_NAME --platform linux/amd64 "$DIRECTORY"

# Run the Docker container to create the layer
docker run --name lambda-layer-container lambda-layer

# Create layers directory, if not created.
mkdir -p "$DIRECTORY/layers"

# Copy the zip file from the container to a local dir
docker cp lambda-layer-container:/app/$LAYER_NAME.zip $DIRECTORY/layers/$LAYER_NAME.zip

# Stop the conainer
docker stop lambda-layer-container

# Remove the running conainer
docker rm lambda-layer-container

# Cleanup: remove the Docker image
docker rmi --force lambda-layer

echo "Successfully created layer: $DIRECTORY/layers/$LAYER_NAME.zip"
