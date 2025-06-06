#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input --clear

# Apply database migrations
python manage.py migrate

# Create default data if needed
python add_default_session.py
