#!/usr/bin/env python3
"""
SSL Certificate Monitor - Main Application Entry Point
Run this file to start the Flask web application
"""

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)