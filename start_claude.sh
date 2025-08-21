#!/bin/bash

# Check if tmux session with "claude" exists
if tmux has-session -t claude 2>/dev/null; then
    echo "Found existing Claude session, attaching..."
    tmux attach-session -t claude
else
    echo "No Claude session found, starting new one..."
    tmux new-session -d -s claude -c /home/er/lsh
    tmux send-keys -t claude "claude-code" Enter
    tmux attach-session -t claude
fi