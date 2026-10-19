#!/bin/bash
# Helper script for Docker Compose profile-based development
# Usage: ./scripts/dev.sh {front|back|full|async|livekit|proxy|all}

set -e

case "$1" in
  front)
    echo "🎨 Starting Frontend only..."
    docker compose --profile front up
    ;;
  back)
    echo "⚙️  Starting Backend (Django + PostgreSQL + Redis)..."
    docker compose --profile back up
    ;;
  full)
    echo "🚀 Starting Frontend + Backend + LiveKit (required for child voice/chat room)..."
    docker compose --profile front --profile back --profile livekit up
    ;;
  async)
    echo "📨 Starting Backend + Async services (RabbitMQ + Celery)..."
    docker compose --profile back --profile async up
    ;;
  livekit)
    echo "🎙️  Starting LiveKit server..."
    docker compose --profile livekit up
    ;;
  proxy)
    echo "🔀 Starting Nginx proxy..."
    docker compose --profile proxy up
    ;;
  all)
    echo "🌟 Starting ALL services..."
    docker compose --profile all up
    ;;
  down)
    echo "🛑 Stopping all services..."
    docker compose down
    ;;
  build)
    echo "🔨 Building services..."
    shift
    if [ -z "$1" ]; then
      docker compose build
    else
      case "$1" in
        front)
          docker compose --profile front build
          ;;
        back)
          docker compose --profile back build
          ;;
        all)
          docker compose --profile all build
          ;;
        *)
          docker compose build "$1"
          ;;
      esac
    fi
    ;;
  *)
    echo "Usage: ./scripts/dev.sh {front|back|full|async|livekit|proxy|all|down|build}"
    echo ""
    echo "Profiles:"
    echo "  front   - Frontend only (React + Vite)"
    echo "  back    - Backend only (Django + PostgreSQL + Redis)"
    echo "  full    - Frontend + Backend + LiveKit + agent (use for conversation page)"
    echo "  async   - Backend + Async services (RabbitMQ + Celery)"
    echo "  livekit - LiveKit server"
    echo "  proxy   - Nginx reverse proxy"
    echo "  all     - All services"
    echo ""
    echo "Commands:"
    echo "  down    - Stop all services"
    echo "  build   - Build services (optionally specify profile)"
    exit 1
    ;;
esac
