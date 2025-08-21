#!/bin/bash
# MyCobot320 Web Controller Management Script
#
# Usage: ./manage_app.sh [start|stop|restart|status|logs]

APP_SESSION="mycobot-app"
APP_DIR="/home/er/lsh"
APP_COMMAND="python app.py"

case "$1" in
    start)
        echo "🚀 Starting MyCobot320 Web Controller..."
        if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
            echo "⚠️  Application already running in session '$APP_SESSION'"
            echo "   Use 'restart' to restart or 'status' to check"
        else
            tmux new-session -d -s "$APP_SESSION" -c "$APP_DIR"
            tmux send-keys -t "$APP_SESSION" "$APP_COMMAND" Enter
            sleep 3
            echo "✅ Application started!"
            echo "🌐 Server running on http://0.0.0.0:5000"
        fi
        ;;
    
    stop)
        echo "⏹️  Stopping MyCobot320 Web Controller..."
        if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
            tmux send-keys -t "$APP_SESSION" C-c
            sleep 2
            tmux kill-session -t "$APP_SESSION" 2>/dev/null
            echo "✅ Application stopped!"
        else
            echo "ℹ️  Application not running"
        fi
        ;;
    
    restart)
        echo "🔄 Restarting MyCobot320 Web Controller..."
        # Stop if running
        if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
            tmux send-keys -t "$APP_SESSION" C-c
            sleep 2
        fi
        
        # Start (create session if needed)
        if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
            tmux send-keys -t "$APP_SESSION" "$APP_COMMAND" Enter
        else
            tmux new-session -d -s "$APP_SESSION" -c "$APP_DIR"
            tmux send-keys -t "$APP_SESSION" "$APP_COMMAND" Enter
        fi
        
        sleep 3
        echo "✅ Application restarted!"
        echo "🌐 Server running on http://0.0.0.0:5000"
        ;;
    
    status)
        echo "📊 MyCobot320 Web Controller Status:"
        if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
            echo "✅ Session '$APP_SESSION' is running"
            
            # Check if app is actually responding (look for recent activity or startup message)
            output=$(tmux capture-pane -t "$APP_SESSION" -p)
            if echo "$output" | grep -q "Running on\|GET /\|POST /"; then
                echo "🌐 Server appears to be running on port 5000"
                # Show last activity
                last_request=$(echo "$output" | grep -E "GET /|POST /" | tail -1 | cut -d' ' -f5-)
                if [ ! -z "$last_request" ]; then
                    echo "📡 Last activity: $last_request"
                fi
            else
                echo "⚠️  Session exists but server may not be running"
            fi
        else
            echo "❌ Session '$APP_SESSION' not found"
        fi
        ;;
    
    logs)
        echo "📋 Showing application logs (Ctrl+C to exit)..."
        if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
            tmux attach-session -t "$APP_SESSION"
        else
            echo "❌ Application not running"
        fi
        ;;
    
    *)
        echo "MyCobot320 Web Controller Management Script"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the application"
        echo "  stop    - Stop the application" 
        echo "  restart - Restart the application"
        echo "  status  - Check application status"
        echo "  logs    - View application logs (attach to tmux session)"
        echo ""
        echo "Examples:"
        echo "  $0 start     # Start the app"
        echo "  $0 restart   # Restart the app"
        echo "  $0 status    # Check if running"
        echo "  $0 logs      # View logs"
        exit 1
        ;;
esac