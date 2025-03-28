#!/bin/bash

# turn on bash's job control
set -m

# Start main process in the background
jac jvserve main.jac &

# Create JIVAS_FILES_ROOT_PATH if it doesn't exist
if [ ! -d "$JIVAS_FILES_ROOT_PATH" ]; then
    mkdir -p $JIVAS_FILES_ROOT_PATH
fi

# Launch file server if in development mode
if [ "$JIVAS_ENVIRONMENT" == "development" ]; then
    echo "Starting file server..."
    jac jvfileserve $JIVAS_FILES_ROOT_PATH &
fi

# Run init script
function initialize() {
    if lsof -i :8000 >/dev/null; then
        # Try to login first
        JIVAS_TOKEN=$(curl --silent --show-error --no-progress-meter \
        --request POST \
        --header 'Content-Type: application/json' \
        --header 'Accept: application/json' \
        --data '{"password": "'$JIVAS_PASSWORD'","email": "'$JIVAS_USER'"}' \
        "http://localhost:8000/user/login" | jq -r '.token')

        echo $JIVAS_TOKEN

        # Check if login was successful
        if [ -z "$JIVAS_TOKEN" ] || [ "$JIVAS_TOKEN" == "null" ]; then
            echo "Login failed. Creating system admin..."

            # Create system admin
            jac create_system_admin main.jac --email $JIVAS_USER --password $JIVAS_PASSWORD

            # Attempt to login again after creating the superadmin
            JIVAS_TOKEN=$(curl --silent --show-error --no-progress-meter \
            --request POST \
            --header 'Content-Type: application/json' \
            --header 'Accept: application/json' \
            --data '{"password": "'$JIVAS_PASSWORD'","email": "'$JIVAS_USER'"}' \
            "http://localhost:8000/user/login" | jq -r '.token')
        fi

        # Print token
        echo "Jivas token: $JIVAS_TOKEN"

        echo "Initializing jivas graph..."

        # Initialize agents
        curl --silent --show-error --no-progress-meter \
        --request POST \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $JIVAS_TOKEN" \
        --data '{}' \
        "http://localhost:8000/walker/init_agents"

        fg %1

    else
        echo "Server is not running on port 8000. Waiting..."
    fi
}

# Main loop to check if a process is running on port 8000
while true; do
    initialize
    sleep 2  # Wait for 2 seconds before checking again
done
