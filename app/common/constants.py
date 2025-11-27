"""
Global constants for the application.

This module defines in-memory storage and user identification for development.
In production, these should be replaced with proper database and authentication.
"""
import uuid

# In-memory file storage simulation
# Structure: {user_uuid: [{'filename': str, 'content': bytes, 'mime_type': str}]}
# Production replacement: PostgreSQL + Redis cache + S3/GCS blob storage
PROJECT_FILE_STORE: dict[str, list[dict]] = {}

# Simulated user identifier (single user for development)
# Production replacement: JWT-based authentication with user sessions
user_uuid: str = str(uuid.uuid4())


