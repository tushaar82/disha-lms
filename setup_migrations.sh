#!/bin/bash

# Setup script to create migrations in the correct order
# This ensures dependencies are resolved properly

echo "Creating migrations for Disha LMS..."
echo ""

# Step 1: Create accounts migrations first (no dependencies)
echo "1. Creating accounts app migrations..."
python manage.py makemigrations accounts

# Step 2: Create core migrations (depends on accounts)
echo ""
echo "2. Creating core app migrations..."
python manage.py makemigrations core

# Step 3: Create API migrations (if any)
echo ""
echo "3. Creating api app migrations..."
python manage.py makemigrations api

# Step 4: Run all migrations
echo ""
echo "4. Running all migrations..."
python manage.py migrate

echo ""
echo "✅ Migrations complete!"
echo ""
echo "Next steps:"
echo "  1. Create a superuser: python manage.py createsuperuser"
echo "  2. Build Tailwind CSS: npm run build:css"
echo "  3. Run the server: python manage.py runserver"
