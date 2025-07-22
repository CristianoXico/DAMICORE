#!/bin/bash

# DAMICORE Docker Build Script
# Builds the optimized Docker image with all latest dependencies

set -e

echo "🚀 DAMICORE Docker Build Script v2.0"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="damicore"
IMAGE_TAG="2.0"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${BLUE}📋 Build Configuration:${NC}"
echo -e "   Image: ${FULL_IMAGE_NAME}"
echo -e "   Python: 3.11"
echo -e "   Features: checkpoint, resume, streaming, ultra-large-files"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Clean up previous builds (optional)
echo -e "${YELLOW}🧹 Cleaning up previous builds...${NC}"
docker system prune -f --volumes > /dev/null 2>&1 || true

# Build the image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build \
    --no-cache \
    --progress=plain \
    --tag "${FULL_IMAGE_NAME}" \
    --tag "${IMAGE_NAME}:latest" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    
    # Display image information
    echo -e "${BLUE}📊 Image Information:${NC}"
    docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo ""
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    echo -e "${BLUE}💡 Usage examples:${NC}"
    echo -e "   Run with docker-compose: ${YELLOW}docker-compose up${NC}"
    echo -e "   Run directly: ${YELLOW}docker run -it --rm -v \$(pwd)/data:/app/data ${FULL_IMAGE_NAME}${NC}"
    echo -e "   Run with external drive: ${YELLOW}docker run -it --rm -v /path/to/external:/app/external_drive ${FULL_IMAGE_NAME}${NC}"
    
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

# Optional: Test the image
echo ""
read -p "🧪 Do you want to test the image? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🧪 Testing Docker image...${NC}"
    docker run --rm "${FULL_IMAGE_NAME}" --help || true
    echo -e "${GREEN}✅ Image test completed${NC}"
fi

echo ""
echo -e "${GREEN}🚀 DAMICORE Docker image is ready for use!${NC}"
