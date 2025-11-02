#!/bin/bash

# Setup script for creating a master account for Phase 5 testing

echo "=========================================="
echo "Creating Master Account for Phase 5 Testing"
echo "=========================================="
echo ""

# Create master account
python manage.py create_master_account

echo ""
echo "=========================================="
echo "Master Account Setup Complete!"
echo "=========================================="
echo ""
echo "Login credentials:"
echo "  Email: master@example.com"
echo "  Password: master123"
echo ""
echo "Test URLs:"
echo "  Login: http://127.0.0.1:8000/accounts/login/"
echo "  Centers: http://127.0.0.1:8000/centers/"
echo "  API: http://127.0.0.1:8000/api/v1/centers/"
echo ""
echo "After login, you will be redirected to the Centers page."
echo "=========================================="
