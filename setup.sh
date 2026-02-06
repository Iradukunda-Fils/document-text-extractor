#!/usr/bin/env bash
# Quick Setup Script for DocuExtract Pro

echo "🚀 DocuExtract Pro - Quick Setup"
echo "================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate venv and install dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Make extract script executable
chmod +x extract

echo ""
echo "✅ Setup complete!"
echo ""
echo "Quick Start:"
echo "  1. Extract text from a file:"
echo "     ./extract path/to/document.pdf"
echo ""
echo "  2. Run Streamlit app:"
echo "     make run-app"
echo ""
echo "  3. Run with OCR:"
echo "     ./extract path/to/scanned.pdf --ocr"
echo ""
echo "  4. See all commands:"
echo "     make help"
echo ""
