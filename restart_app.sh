#!/bin/bash
# MyCobot320 Web Controller Restart Script
#
# This script properly stops and restarts the web controller application
# running in the tmux session.

APP_SESSION="mycobot-app"
APP_DIR="/home/er/lsh"
APP_COMMAND="python app.py"

echo "🔄 Restarting MyCobot320 Web Controller..."

# Check if session exists
if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
    echo "📋 Found existing session '$APP_SESSION'"
    
    # Stop the current app
    echo "⏹️  Stopping current application..."
    tmux send-keys -t "$APP_SESSION" C-c
    sleep 2
    
    # Check if session still exists (it might have closed)
    if tmux has-session -t "$APP_SESSION" 2>/dev/null; then
        echo "🔄 Restarting in existing session..."
        tmux send-keys -t "$APP_SESSION" "$APP_COMMAND" Enter
    else
        echo "📋 Session closed, creating new session..."
        tmux new-session -d -s "$APP_SESSION" -c "$APP_DIR"
        tmux send-keys -t "$APP_SESSION" "$APP_COMMAND" Enter
    fi
else
    echo "🆕 Creating new session '$APP_SESSION'..."
    tmux new-session -d -s "$APP_SESSION" -c "$APP_DIR"
    tmux send-keys -t "$APP_SESSION" "$APP_COMMAND" Enter
fi

# Wait a moment for startup
sleep 3

# Check if app started successfully
if tmux capture-pane -t "$APP_SESSION" -p | grep -q "Running on"; then
    echo "✅ Application restarted successfully!"
    echo "🌐 Server running on http://0.0.0.0:5000"
    echo "📺 To view logs: tmux attach-session -t $APP_SESSION"
else
    echo "❌ Application may have failed to start. Check logs:"
    echo "   tmux attach-session -t $APP_SESSION"
fi

echo "🎯 To attach to session: tmux attach-session -t $APP_SESSION"
echo "🔍 To view sessions: tmux list-sessions"