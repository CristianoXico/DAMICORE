#!/bin/bash

# DAMICORE Docker Deployment Script
# Deploys and manages the DAMICORE pipeline container

set -e

echo "🚀 DAMICORE Docker Deployment Script v2.0"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="damicore"

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [COMMAND]${NC}"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}up${NC}          Start DAMICORE pipeline"
    echo -e "  ${GREEN}down${NC}        Stop DAMICORE pipeline"
    echo -e "  ${GREEN}restart${NC}     Restart DAMICORE pipeline"
    echo -e "  ${GREEN}logs${NC}        Show pipeline logs"
    echo -e "  ${GREEN}status${NC}      Show pipeline status"
    echo -e "  ${GREEN}shell${NC}       Open shell in container"
    echo -e "  ${GREEN}monitor${NC}     Start with monitoring"
    echo -e "  ${GREEN}clean${NC}       Clean up containers and volumes"
    echo -e "  ${GREEN}help${NC}        Show this help message"
}

# Function to check prerequisites
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}❌ docker-compose.yml not found${NC}"
        exit 1
    fi
}

# Function to create required directories
create_directories() {
    echo -e "${BLUE}📁 Creating required directories...${NC}"
    mkdir -p input results data temp logs external_drive damicore_analysis
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Function to start the pipeline
start_pipeline() {
    echo -e "${BLUE}🚀 Starting DAMICORE pipeline...${NC}"
    create_directories
    docker-compose up -d $SERVICE_NAME
    echo -e "${GREEN}✅ Pipeline started successfully${NC}"
    echo -e "${YELLOW}💡 Use 'docker-compose logs -f damicore' to follow logs${NC}"
}

# Function to start with monitoring
start_with_monitoring() {
    echo -e "${BLUE}🚀 Starting DAMICORE pipeline with monitoring...${NC}"
    create_directories
    docker-compose --profile monitoring up -d
    echo -e "${GREEN}✅ Pipeline and monitoring started${NC}"
    echo -e "${YELLOW}💡 Monitoring available at: http://localhost:9100${NC}"
}

# Function to stop the pipeline
stop_pipeline() {
    echo -e "${BLUE}🛑 Stopping DAMICORE pipeline...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Pipeline stopped${NC}"
}

# Function to restart the pipeline
restart_pipeline() {
    echo -e "${BLUE}🔄 Restarting DAMICORE pipeline...${NC}"
    docker-compose restart $SERVICE_NAME
    echo -e "${GREEN}✅ Pipeline restarted${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Showing DAMICORE logs...${NC}"
    docker-compose logs -f $SERVICE_NAME
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 DAMICORE Pipeline Status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${BLUE}📈 Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

# Function to open shell
open_shell() {
    echo -e "${BLUE}🐚 Opening shell in DAMICORE container...${NC}"
    docker-compose exec $SERVICE_NAME /bin/bash
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up containers and volumes...${NC}"
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main script logic
check_prerequisites

case "${1:-help}" in
    "up")
        start_pipeline
        ;;
    "down")
        stop_pipeline
        ;;
    "restart")
        restart_pipeline
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "shell")
        open_shell
        ;;
    "monitor")
        start_with_monitoring
        ;;
    "clean")
        cleanup
        ;;
    "help"|*)
        show_usage
        ;;
esac
