#!/bin/bash

# Populate Database Script for Disha LMS
# Creates test data for a computer training institute

set -e  # Exit on error

echo "=============================================================="
echo "🚀 Disha LMS - Database Population Script"
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
        echo "   python -m venv venv"
        echo "   source venv/bin/activate"
        exit 1
    fi
fi

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Error: Django is not installed!"
    echo "Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Confirm with user
echo "⚠️  WARNING: This script will populate the database with test data."
echo ""
echo "📋 What will be created:"
echo "   • 5 Centers in Indian cities (Mumbai, Delhi, Bangalore, etc.)"
echo "   • 5 Center Heads with Indian names"
echo "   • 8 Programming Subjects (Python, Java, C++, Web Dev, etc.)"
echo "   • 100+ Topics across all subjects"
echo "   • 15-25 Faculty members"
echo "   • 75-125 Students with Indian names"
echo "   • 150-300 Subject assignments"
echo "   • 3 months of attendance records (1000+ records)"
echo ""
echo "🔐 Default Passwords:"
echo "   • Master: master123"
echo "   • Center Heads: head123"
echo "   • Faculty: faculty123"
echo ""

read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled."
    exit 0
fi

echo ""
echo "🔄 Running database population script..."
echo ""

# Run the Python script
python3 populate_test_data.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================================="
    echo "✅ Database populated successfully!"
    echo "=============================================================="
    echo ""
    echo "🎯 Next Steps:"
    echo "   1. Start the development server:"
    echo "      python manage.py runserver"
    echo ""
    echo "   2. Access the application:"
    echo "      http://127.0.0.1:8000/"
    echo ""
    echo "   3. Login with master account:"
    echo "      Username: master"
    echo "      Password: master123"
    echo ""
    echo "   4. Explore the dashboards:"
    echo "      • Master Dashboard: View all centers"
    echo "      • Center Dashboard: View center statistics"
    echo "      • Faculty Dashboard: View teaching analytics"
    echo "      • Student Reports: View learning progress"
    echo ""
    echo "=============================================================="
else
    echo ""
    echo "❌ Error: Database population failed!"
    echo "Please check the error messages above."
    exit 1
fi
