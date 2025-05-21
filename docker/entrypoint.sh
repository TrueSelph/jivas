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
echo "JIVAS_BASE_URL: $JIVAS_BASE_URL"
echo "JIVAS_STUDIO_URL: $JIVAS_STUDIO_URL"
echo "JIVAS_FILES_URL: $JIVAS_FILES_URL"
echo "JIVAS_ENVIRONMENT: $JIVAS_ENVIRONMENT"
echo "--------------------------------"

# turn on bash's job control
set -m

# Start main process in the background
jvcli server launch &

# Create JIVAS_FILES_ROOT_PATH if it doesn't exist
if [ ! -d "$JIVAS_FILES_ROOT_PATH" ]; then
    mkdir -p $JIVAS_FILES_ROOT_PATH
fi

# Launch file server if in development mode and JIVAS_FILEINTERFACE is set to local
if [ "$JIVAS_ENVIRONMENT" == "development" ] && [ "$JIVAS_FILEINTERFACE" == "local" ]; then
    echo "Starting file server..."
    jac jvfileserve $JIVAS_FILES_ROOT_PATH &
elif [ "$JIVAS_ENVIRONMENT" == "production" ] && [ "$JIVAS_FILEINTERFACE" == "s3" ]; then
    echo "Starting proxy server..."
    jac jvproxyserve &
else
    echo "File server not started. JIVAS_ENVIRONMENT: $JIVAS_ENVIRONMENT, JIVAS_FILEINTERFACE: $JIVAS_FILEINTERFACE"
fi

# Rest of script remains unchanged
function initialize() {
    if lsof -i :8000 >/dev/null; then
        # Try to login first using jvcli
        echo "Attempting to login with jvcli..."
        LOGIN_OUTPUT=$(jvcli server login --email "$JIVAS_USER" --password "$JIVAS_PASSWORD" 2>&1)

        # Extract token from login output
        JIVAS_TOKEN=$(echo "$LOGIN_OUTPUT" | grep "Token:" | sed 's/Token: //')

        echo $JIVAS_TOKEN

        # Check if login was successful
        if [ -z "$JIVAS_TOKEN" ] || [ "$JIVAS_TOKEN" == "null" ]; then
            echo "Login failed. Creating system admin..."

            jvcli server createadmin

            # Attempt to login again after creating the superadmin
            LOGIN_OUTPUT=$(jvcli server login --email "$JIVAS_USER" --password "$JIVAS_PASSWORD" 2>&1)

            # Extract token from login output
            JIVAS_TOKEN=$(echo "$LOGIN_OUTPUT" | grep "Token:" | sed 's/Token: //')
            echo $JIVAS_TOKEN
        fi

        # Print token
        echo "Jivas token: $JIVAS_TOKEN"

        echo "Initializing jivas graph..."

        # Initialize agents
        jvcli server initagents

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