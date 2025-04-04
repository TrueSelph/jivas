#!/bin/bash

# Function to export variables from .env file
export_env_vars() {
    if [ -f ".env" ]; then
        echo "Loading environment variables from .env file..."
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ ! "$line" =~ ^(#.*)?$ ]] && [ -n "$line" ]; then
                # Extract variable name and value
                varname=$(echo "$line" | cut -d= -f1)
                varvalue=$(echo "$line" | cut -d= -f2-)

                # Remove quotes if present
                varvalue=$(echo "$varvalue" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

                # Export the variable
                export "$varname"="$varvalue"
                echo "Exported: $varname=$varvalue"
            fi
        done < .env
    else
        echo "Warning: No .env file found. Using environment variables from Docker or system defaults."
    fi
}

# Export variables
export_env_vars

# Log the configuration
echo "Starting Jivas with configuration:"
echo "--------------------------------"
echo "JIVAS_USER: $JIVAS_USER"
echo "JIVAS_PORT: $JIVAS_PORT"
echo "JIVAS_BASE_URL: $JIVAS_BASE_URL"
echo "JIVAS_STUDIO_URL: $JIVAS_STUDIO_URL"
echo "JIVAS_FILES_URL: $JIVAS_FILES_URL"
echo "JIVAS_ENVIRONMENT: $JIVAS_ENVIRONMENT"
echo "--------------------------------"

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

# Rest of script remains unchanged
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

            # if DATABASE_HOST is set create system admin, if not use signup
            if [ -z "$DATABASE_HOST" ]; then
                echo "Database host is not set. Using signup endpoint"
                curl --silent --show-error --no-progress-meter \
                    --request POST \
                    --header 'Content-Type: application/json' \
                    --header 'Accept: application/json' \
                    --data '{
                    "password": "'"$JIVAS_PASSWORD"'",
                    "email": "'"$JIVAS_USER"'"
                    }' \
                    "http://localhost:$JIVAS_PORT/user/register"
            else
                echo "Creating system admin..."
                jac create_system_admin main.jac --email $JIVAS_USER --password $JIVAS_PASSWORD
            fi

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