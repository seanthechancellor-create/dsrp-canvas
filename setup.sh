#!/bin/bash
#
# DSRP Canvas Setup Script
#
# This script sets up and starts all DSRP Canvas services.
# Run with: ./setup.sh [command]
#
# Commands:
#   start     - Start all services (default)
#   stop      - Stop all services
#   restart   - Restart all services
#   status    - Check service status
#   logs      - View service logs
#   init      - Initialize databases and vector store
#   test      - Run tests
#   clean     - Remove all data and containers
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Print colored message
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is not installed. Please install it first."
        return 1
    fi
    return 0
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    local missing=()

    if ! check_command docker; then
        missing+=("docker")
    fi

    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        missing+=("docker-compose")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing prerequisites: ${missing[*]}"
        echo ""
        echo "Installation instructions:"
        echo "  Docker: https://docs.docker.com/get-docker/"
        echo "  Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi

    success "All prerequisites installed"
}

# Get docker compose command (supports both docker-compose and docker compose)
get_compose_cmd() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
    elif docker-compose --version &> /dev/null; then
        echo "docker-compose"
    else
        error "Docker Compose not found"
        exit 1
    fi
}

# Setup environment file
setup_env() {
    if [ ! -f .env ]; then
        info "Creating .env file from .env.example..."
        cp .env.example .env
        warn "Please edit .env and add your API keys:"
        echo "  - ANTHROPIC_API_KEY (required for DSRP analysis)"
        echo "  - OPENAI_API_KEY (required for vector embeddings)"
        echo ""
        echo "Run: nano .env"
        return 1
    fi

    # Check for required keys
    local missing_keys=()

    if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
        if ! grep -q "ANTHROPIC_API_KEY=.*[a-zA-Z0-9]" .env 2>/dev/null || grep -q "ANTHROPIC_API_KEY=your_" .env 2>/dev/null; then
            missing_keys+=("ANTHROPIC_API_KEY")
        fi
    fi

    if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        if ! grep -q "OPENAI_API_KEY=.*[a-zA-Z0-9]" .env 2>/dev/null || grep -q "OPENAI_API_KEY=your_" .env 2>/dev/null; then
            missing_keys+=("OPENAI_API_KEY")
        fi
    fi

    if [ ${#missing_keys[@]} -gt 0 ]; then
        warn "Missing or invalid API keys in .env: ${missing_keys[*]}"
        warn "Some features may not work without these keys."
    fi

    return 0
}

# Start services
start_services() {
    info "Starting DSRP Canvas services..."

    local compose_cmd=$(get_compose_cmd)

    # Pull latest images
    info "Pulling Docker images..."
    $compose_cmd pull

    # Build custom images
    info "Building backend and frontend..."
    $compose_cmd build

    # Start services
    info "Starting containers..."
    $compose_cmd up -d

    success "Services started!"
    echo ""

    # Wait for services to be ready
    wait_for_services
}

# Wait for services to be healthy
wait_for_services() {
    info "Waiting for services to be ready..."

    local max_attempts=30
    local attempt=1

    # Wait for backend
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            success "Backend is ready"
            break
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        warn "Backend not responding after ${max_attempts} attempts"
    fi

    # Wait for frontend
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            success "Frontend is ready"
            break
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        warn "Frontend not responding after ${max_attempts} attempts"
    fi
}

# Stop services
stop_services() {
    info "Stopping DSRP Canvas services..."
    local compose_cmd=$(get_compose_cmd)
    $compose_cmd down
    success "Services stopped"
}

# Restart services
restart_services() {
    stop_services
    start_services
}

# Show service status
show_status() {
    info "Service Status:"
    echo ""

    local compose_cmd=$(get_compose_cmd)
    $compose_cmd ps

    echo ""
    info "Health Checks:"

    # Backend health
    echo -n "  Backend API: "
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}healthy${NC}"
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || true
    else
        echo -e "${RED}not responding${NC}"
    fi

    # Frontend health
    echo -n "  Frontend: "
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}healthy${NC}"
    else
        echo -e "${RED}not responding${NC}"
    fi

    # Cache health
    echo -n "  Redis Cache: "
    if curl -s http://localhost:8000/api/cache/health 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}healthy${NC}"
    else
        echo -e "${YELLOW}unavailable${NC}"
    fi

    echo ""
    info "Service URLs:"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  MCP Server:   http://localhost:8001"
}

# Show logs
show_logs() {
    local compose_cmd=$(get_compose_cmd)
    local service="${1:-}"

    if [ -n "$service" ]; then
        $compose_cmd logs -f "$service"
    else
        $compose_cmd logs -f
    fi
}

# Initialize databases
init_databases() {
    info "Initializing databases..."

    # Wait for backend to be ready
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            break
        fi
        info "Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        error "Backend not available. Make sure services are running: ./setup.sh start"
        exit 1
    fi

    # Initialize vector store
    info "Initializing vector store (pgvector)..."
    local response=$(curl -s -X POST http://localhost:8000/api/search/initialize)

    if echo "$response" | grep -q "initialized"; then
        success "Vector store initialized"
    else
        warn "Vector store initialization response: $response"
    fi

    # Warmup cache
    info "Warming up cache..."
    response=$(curl -s -X POST http://localhost:8000/api/cache/warmup)

    if echo "$response" | grep -q "warmed"; then
        success "Cache warmed up"
    else
        warn "Cache warmup response: $response"
    fi

    success "Database initialization complete!"
}

# Run tests
run_tests() {
    info "Running tests..."

    local compose_cmd=$(get_compose_cmd)

    # Backend tests
    info "Running backend tests..."
    $compose_cmd exec backend pytest -v || warn "Backend tests failed or not available"

    # Frontend tests
    info "Running frontend tests..."
    $compose_cmd exec frontend npm test -- --run || warn "Frontend tests failed or not available"

    success "Tests complete"
}

# Clean up everything
clean_all() {
    warn "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Cleaning up..."
        local compose_cmd=$(get_compose_cmd)
        $compose_cmd down -v --remove-orphans
        success "Cleanup complete"
    else
        info "Cleanup cancelled"
    fi
}

# Install local dependencies (without Docker)
install_local() {
    info "Installing local dependencies..."

    # Check for Python
    if ! check_command python3; then
        error "Python 3 is required"
        exit 1
    fi

    # Check for Node.js
    if ! check_command node; then
        error "Node.js is required"
        exit 1
    fi

    # Backend dependencies
    info "Installing backend dependencies..."
    cd backend
    python3 -m pip install -r requirements.txt
    cd ..

    # Frontend dependencies
    info "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..

    success "Local dependencies installed"
}

# Start local development (without Docker)
start_local() {
    info "Starting local development servers..."

    # Check for required services
    warn "Make sure these services are running:"
    echo "  - TypeDB on localhost:1729"
    echo "  - PostgreSQL on localhost:5432"
    echo "  - Redis on localhost:6379"
    echo ""

    # Start backend in background
    info "Starting backend..."
    cd backend
    uvicorn app.main:app --reload --port 8000 &
    BACKEND_PID=$!
    cd ..

    # Start frontend
    info "Starting frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    success "Local servers started"
    echo "  Backend PID: $BACKEND_PID"
    echo "  Frontend PID: $FRONTEND_PID"
    echo ""
    echo "Press Ctrl+C to stop"

    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
}

# Print help
print_help() {
    echo "DSRP Canvas Setup Script"
    echo ""
    echo "Usage: ./setup.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start         Start all services (default)"
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  status        Check service status and health"
    echo "  logs [svc]    View logs (optionally for specific service)"
    echo "  init          Initialize databases and vector store"
    echo "  test          Run backend and frontend tests"
    echo "  clean         Remove all containers and data"
    echo "  install       Install local dependencies (without Docker)"
    echo "  local         Start local dev servers (without Docker)"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh                 # Start all services"
    echo "  ./setup.sh start           # Start all services"
    echo "  ./setup.sh logs backend    # View backend logs"
    echo "  ./setup.sh init            # Initialize vector store"
    echo ""
    echo "Service URLs (after start):"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo "  MCP Server:   http://localhost:8001"
}

# Main entry point
main() {
    local command="${1:-start}"

    case "$command" in
        start)
            check_prerequisites
            setup_env
            start_services
            echo ""
            info "Run './setup.sh init' to initialize the vector store"
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_prerequisites
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-}"
            ;;
        init)
            init_databases
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_all
            ;;
        install)
            install_local
            ;;
        local)
            start_local
            ;;
        help|--help|-h)
            print_help
            ;;
        *)
            error "Unknown command: $command"
            echo ""
            print_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
