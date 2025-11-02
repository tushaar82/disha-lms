#!/bin/bash

# Setup Mumbai Learning Center with complete data

set -e

echo "=============================================================="
echo "🏢 Mumbai Learning Center - Complete Setup"
echo "=============================================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Error: venv directory not found!"
        exit 1
    fi
fi

echo "📋 This will create for Mumbai Center:"
echo "   • 25 Students with Indian names"
echo "   • 3-5 Faculty members"
echo "   • Subject assignments"
echo "   • 3 months of backdated attendance"
echo "   • Complete dashboard data"
echo ""

read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🔄 Running setup..."
echo ""

python3 populate_mumbai_center.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================================="
    echo "✅ Mumbai Center Setup Complete!"
    echo "=============================================================="
    echo ""
    echo "🎯 Access your data:"
    echo "   • Mumbai Dashboard: http://127.0.0.1:8000/centers/dashboard/"
    echo "   • Students List: http://127.0.0.1:8000/students/"
    echo "   • Faculty Dashboard: http://127.0.0.1:8000/faculty/dashboard/"
    echo ""
    echo "🔐 Login as:"
    echo "   • Master: master@dishalms.com / master123"
    echo "   • Faculty: faculty.mumbai.1@dishalms.com / faculty123"
    echo ""
    echo "=============================================================="
else
    echo "❌ Setup failed!"
    exit 1
fi
