"""
Pytest configuration for hplc-chromatography-peak-resolver test suite.
"""
import os

# Set required environment variable for audit trail before any agent imports
os.environ.setdefault("AUDIT_SECRET_KEY", "test-secret-key-for-pytest-min-32-chars-long")
