# Jivas Docker Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| JIVAS_USER | admin@jivas.com | Admin user email |
| JIVAS_PASSWORD | password | Admin user password |
| JIVAS_PORT | 8000 | Port for the main Jivas service |
| JIVAS_BASE_URL | http://localhost:8000 | Base URL for API |
| JIVAS_STUDIO_URL | http://localhost:8989 | URL for Studio UI |
| JIVAS_FILES_URL | http://localhost:9000/files | URL for file server |
| JIVAS_DESCRIPTOR_ROOT_PATH | .jvdata | Path for descriptor data |
| JIVAS_ACTIONS_ROOT_PATH | actions | Path for actions |
| JIVAS_DAF_ROOT_PATH | daf | Path for DAF (Digital Agent File) |
| JIVAS_FILES_ROOT_PATH | .files | Path for files storage |
| JIVAS_WEBHOOK_SECRET_KEY | ABCDEFGHIJK | Secret key for webhooks |
| JIVAS_ENVIRONMENT | development | Environment (development/production) |

## Running with S3 file storage

The file interface can be configured using environment variables:

| Environment Variable | Value | Description |
|---------------------|--------|-------------|
| JIVAS_FILE_INTERFACE | "local" or "s3" | Selects the storage backend to use - either local filesystem or S3 |
| JIVAS_S3_BUCKET_NAME | "my-bucket" | Name of the S3 bucket to use for storage when using S3 backend |
| JIVAS_S3_REGION_NAME | "us-east-1" | AWS region for S3 bucket (defaults to us-east-1) |
| JIVAS_S3_ACCESS_KEY_ID | "access-key" | AWS access key ID for S3 authentication |
| JIVAS_S3_SECRET_ACCESS_KEY | "secret-key" | AWS secret access key for S3 authentication |
| JIVAS_S3_ENDPOINT_URL | "https://..." | Optional custom S3 endpoint URL |
| JIVAS_FILES_ROOT_PATH | ".files" | Root directory path for file storage |

## Running with custom configuration

```bash
docker run -p 8000:8000 -p 8989:8989 -p 9000:9000 -p 8501:8501 \
  -e JIVAS_USER=custom@example.com \
  -e JIVAS_PASSWORD=strongpassword \
  -e JIVAS_ENVIRONMENT=development \
  ghcr.io/trueselph/jivas:latest
```

or using .env file:

```bash
docker run --env-file .env -p 8000:8000 -p 8989:8989 -p 9000:9000 -p 8501:8501 \
  ghcr.io/trueselph/jivas:latest
```