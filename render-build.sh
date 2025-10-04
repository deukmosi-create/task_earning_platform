#!/usr/bin/env bash
# Install system dependencies for Pillow
apt-get update
apt-get install -y libjpeg-dev zlib1g-dev

# Then install Python dependencies
pip install -r requirements.txt