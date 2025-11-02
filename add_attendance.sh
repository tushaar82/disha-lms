#!/bin/bash

# Add Backdated Attendance Script for Disha LMS
# Creates 3 months of attendance history for all students

set -e  # Exit on error

echo "=============================================================="
echo "🚀 Disha LMS - Add Backdated Attendance"
echo "=============================================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Activating virtual environment..."
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Error: venv directory not found!"
        echo "Please create a virtual environment first:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        exit 1
    fi
fi

# Check if Django is installed
if ! python3 -c "import django" 2>/dev/null; then
    echo "❌ Error: Django is not installed!"
    echo "Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Confirm with user
echo "⚠️  This script will add backdated attendance for all active students."
echo ""
echo "📋 What will be created:"
echo "   • 3 months of attendance history (last 90 days)"
echo "   • 2-4 sessions per week per student (realistic frequency)"
echo "   • 60-80% attendance rate (realistic dropout/absence)"
echo "   • Random session times (morning/afternoon/evening)"
echo "   • 1-3 topics covered per session"
echo "   • Progress notes for each session"
echo ""
echo "⏱️  Estimated time: 1-5 minutes depending on student count"
echo ""

read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled."
    exit 0
fi

echo ""
echo "🔄 Running attendance generation script..."
echo ""

# Run the Python script
python3 add_backdated_attendance.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================================="
    echo "✅ Backdated attendance added successfully!"
    echo "=============================================================="
    echo ""
    echo "🎯 What to do next:"
    echo "   1. View student dashboards:"
    echo "      http://127.0.0.1:8000/students/"
    echo ""
    echo "   2. Check student reports with charts:"
    echo "      http://127.0.0.1:8000/reports/student/<id>/"
    echo ""
    echo "   3. View faculty dashboards:"
    echo "      http://127.0.0.1:8000/faculty/dashboard/"
    echo ""
    echo "   4. Check attendance history:"
    echo "      http://127.0.0.1:8000/attendance/history/"
    echo ""
    echo "=============================================================="
else
    echo ""
    echo "❌ Error: Attendance generation failed!"
    echo "Please check the error messages above."
    exit 1
fi
