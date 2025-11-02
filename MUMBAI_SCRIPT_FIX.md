# Mumbai Center Script - Multiple Centers Fix

## Issue
Script failed when multiple Mumbai centers exist in database:
```
❌ Error: get() returned more than one Center -- it returned 2!
```

## Root Cause
The script was using:
```python
mumbai_center = Center.objects.get(city='Mumbai')
```

This fails when there are multiple centers in Mumbai city.

## Fix Applied

### New Logic (Priority Order)

1. **Try specific code first** (most specific)
   ```python
   mumbai_center = Center.objects.get(code='DLMUM01')
   ```

2. **If not found, find any Mumbai center** (fallback)
   ```python
   mumbai_centers = Center.objects.filter(city='Mumbai', is_deleted=False)
   if mumbai_centers.exists():
       # Use the first one
       mumbai_center = mumbai_centers.first()
   ```

3. **If none exist, create new** (last resort)
   ```python
   mumbai_center = Center.objects.create(
       name='Mumbai Learning Center',
       code='DLMUM01',
       ...
   )
   ```

## Expected Behavior

### Scenario 1: DLMUM01 exists
```
📍 Finding Mumbai Center...
✅ Found: Mumbai Learning Center (DLMUM01)
```

### Scenario 2: DLMUM01 not found, but other Mumbai centers exist
```
📍 Finding Mumbai Center...
❌ Mumbai center (DLMUM01) not found!

⚠️  Found 2 Mumbai center(s):
   1. Disha Learning Center - Mumbai (DLMUM02)
   2. Mumbai Tech Center (DLMUM03)

Using the first one...
✅ Selected: Disha Learning Center - Mumbai (DLMUM02)
```

### Scenario 3: No Mumbai centers exist
```
📍 Finding Mumbai Center...
❌ Mumbai center (DLMUM01) not found!
Creating Mumbai center...
✅ Created: Mumbai Learning Center
```

## Why This Matters

### Production Scenario
In production, you might have:
- Multiple branches in same city
- Test centers and production centers
- Historical centers (soft-deleted)
- Renamed centers

### The Fix Handles
✅ Multiple centers in same city  
✅ Specific center selection by code  
✅ Graceful fallback to any Mumbai center  
✅ Auto-creation if none exist  
✅ Excludes soft-deleted centers  

## Testing

### Test with Multiple Centers
```bash
# Create multiple Mumbai centers first
python manage.py shell
>>> from apps.centers.models import Center
>>> Center.objects.filter(city='Mumbai').count()
2

# Now run the script
./setup_mumbai.sh
```

### Test with No Centers
```bash
# Delete all Mumbai centers
python manage.py shell
>>> from apps.centers.models import Center
>>> Center.objects.filter(city='Mumbai').delete()

# Script will create DLMUM01
./setup_mumbai.sh
```

## Files Modified

**`populate_mumbai_center.py`**
- Changed from `get(city='Mumbai')` to `get(code='DLMUM01')`
- Added fallback logic for multiple centers
- Added user-friendly messages
- Proper error handling

## Status

✅ **Fixed and Ready**

The script now:
- Handles multiple Mumbai centers gracefully
- Uses specific center code for precision
- Falls back intelligently
- Creates center if needed
- Shows clear messages to user

---

**Date**: 2025-11-02  
**Version**: 1.1  
**Status**: ✅ Production Ready
