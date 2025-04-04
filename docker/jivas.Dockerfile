# Use a slim Python image as the base
FROM python:3.12-slim
ARG JIVAS_VERSION

# Set the working directory
WORKDIR /app

# Install system dependencies (static layers for caching)
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential git supervisor lsof curl jq bash \
	&& rm -rf /var/lib/apt/lists/*

# Setup logging (likely not to change, so place it early)
RUN mkdir -p /tmp/jac_cloud_logs && chmod 777 /tmp/jac_cloud_logs

# Install the plugins
RUN pip install --upgrade pip
RUN pip install git+https://github.com/TrueSelph/jaseci.git@fast_import_v2#subdirectory=jac
RUN pip install jivas==$JIVAS_VERSION

# init project files
RUN jvcli startproject .

# Parser generation
RUN jac tool gen_parser

# Add JACPATH to the environment
ENV JACPATH=/app

# Copy the supervisord configuration (less likely to change frequently)
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy the entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Start the supervisor
CMD ["/usr/bin/supervisord"]
