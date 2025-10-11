#!/bin/bash

# Setup script for Polymarket Trading Agent

set -e

echo "========================================="
echo "Polymarket Trading Agent Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi
echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create directories
echo "Creating directories..."
mkdir -p logs
mkdir -p data/logs
echo "✓ Directories created"
echo ""

# Setup .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - TAVILY_API_KEY"
    echo "   - EMAIL_* (for email reports)"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: python main.py --test"
echo "3. Check the email report"
echo "4. For production: python main.py --schedule"
echo ""
echo "For help: python main.py --help"
echo ""
