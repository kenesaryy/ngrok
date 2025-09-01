#!/bin/bash
# Deploy to Azure Container Registry

set -e

# Validate environment argument
if [ $# -ne 1 ]; then
    echo "Error: Environment argument required (prod or staging)"
    exit 1
fi

ENV=$1

if [ "$ENV" != "prod" ] && [ "$ENV" != "staging" ]; then
    echo "Error: Environment must be either 'prod' or 'staging'"
    exit 1
fi

SERVICE=test                       # имя образа (фиксированное)
ACR_NAME=zenlibrary$ENV            # имя ACR, зависит от окружения
VERSION=$(openssl rand -hex 8)     # случайный тег
IMAGE_TAG=$ACR_NAME.azurecr.io/$SERVICE:$VERSION
PLATFORM=linux/amd64

echo "Starting build & push for $SERVICE into $ENV..."

echo "Logging in to Azure Container Registry: $ACR_NAME"
az acr login --name $ACR_NAME

echo "Using version tag: $VERSION"

echo "Docker building $SERVICE"
docker build --platform $PLATFORM -t $SERVICE .

echo "Docker tagging $SERVICE for Azure Container Registry"
docker tag $SERVICE $IMAGE_TAG

echo "Docker push to Azure Container Registry: $IMAGE_TAG"
docker push $IMAGE_TAG

echo "Image pushed to Azure Container Registry successfully: $IMAGE_TAG"