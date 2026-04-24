#!/bin/bash

# MSVAI Weekly Reports - Quick Setup Script
# This script automates the setup process for new Mac devices

set -e  # Exit on any error

echo "🚀 MSVAI Weekly Reports - Quick Setup"
echo "======================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "📥 Installing dependencies manually..."
    pip install pytz slack_sdk langdetect requests
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env file from template..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your actual credentials!"
    else
        echo "📝 Creating basic .env file..."
        cat > .env << 'EOF'
# Slack User Token (required)
SLACK_USER_TOKEN=xoxp-your-slack-user-token-here

# OpenRouter API Key (optional, for AI replies)
OPENROUTER_API_KEY=your-openrouter-api-key-here
EOF
        echo "⚠️  Please edit .env file with your actual credentials!"
    fi
else
    echo "✅ .env file already exists"
fi

# Create reports directory
mkdir -p reports

# Run verification
echo ""
echo "🔍 Running setup verification..."
python verify_setup.py

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Slack token"
echo "2. Test with: python jobs/check_weekly_reports.py --help"
echo "3. Run verification again: python verify_setup.py"