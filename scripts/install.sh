#!/bin/bash
# Installation script for Linux/Mac

set -e

echo "======================================"
echo " Face Tracking Camera - Installation"
echo "======================================"
echo ""

# Check Python
echo "[1/5] Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python not found. Please install Python 3.8+ and try again."
    exit 1
fi

$PYTHON --version
echo "✅ Python found"
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "  Virtual environment already exists (skipping)"
else
    $PYTHON -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate venv and install dependencies
echo "[3/5] Installing Python dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create necessary directories
echo "[4/5] Setting up directories..."
mkdir -p logs models
echo "✅ Directories created"
echo ""

# Check serial port permissions (Linux/Mac only)
if [[ "$OSTYPE" != "darwin"* ]] && [[ "$OSTYPE" != "msys" ]] && [[ "$OSTYPE" != "win32" ]]; then
    echo "[5/5] Checking serial port permissions..."
    if groups | grep -q dialout; then
        echo "✅ You're in the 'dialout' group (serial access OK)"
    else
        echo "⚠️  You may need serial port permissions!"
        echo "   Run: sudo usermod -a -G dialout $USER"
        echo "   Then log out and back in."
    fi
else
    echo "[5/5] Serial port check (skipped on non-Linux)"
fi
echo ""

# Done
echo "======================================"
echo "✅ Installation complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Connect Arduino with servo to USB"
echo "  2. Run calibration: source venv/bin/activate && python scripts/run.py calibrate"
echo "  3. Capture face: source venv/bin/activate && python scripts/run.py capture"
echo "  4. Start tracking: source venv/bin/activate && python scripts/run.py track"
echo ""
echo "For help: python scripts/run.py --help"
echo ""
