# Use a slim Python image as the base
FROM python:3.12-slim AS builder
ARG JIVAS_VERSION

# Set the working directory
WORKDIR /build

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential git curl \
	&& rm -rf /var/lib/apt/lists/*

# Install the plugins with better error handling
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir jivas==$JIVAS_VERSION
RUN pip install --no-cache-dir jvcli==$JIVAS_VERSION
RUN pip install --no-cache-dir jvmanager==$JIVAS_VERSION

# Try to find and run jvcli
RUN jvcli startproject . --no-env

# Parser generation
RUN jac tool gen_parser

# Final runtime stage
FROM python:3.12-slim
ARG JIVAS_VERSION

# Set the working directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
	supervisor lsof curl jq bash \
	&& rm -rf /var/lib/apt/lists/*

# Setup logging
RUN mkdir -p /tmp/jac_cloud_logs && chmod 777 /tmp/jac_cloud_logs

# Copy Python packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the generated project files
COPY --from=builder /build/ /app/

# Add JACPATH to the environment
ENV JACPATH=/app

# Copy the supervisord configuration and entrypoint script
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Start the supervisor
CMD ["/usr/bin/supervisord"]
