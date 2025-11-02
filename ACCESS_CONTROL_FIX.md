# Access Control Fix - Remove All 403 Errors

## Overview
Fixed all 403 Forbidden errors by updating access control mixins and views to allow **Master Account** full system access while maintaining proper role-based restrictions for Center Heads and Faculty.

## Changes Made

### 1. Core Mixins Updated (`apps/core/mixins.py`)

#### CenterHeadRequiredMixin
**Before**: Only Center Heads allowed  
**After**: Master Account + Center Heads

```python
# Master account has access to everything
if request.user.is_master_account:
    return super().dispatch(request, *args, **kwargs)
```

#### FacultyRequiredMixin
**Before**: Only Faculty allowed  
**After**: Master Account + Faculty

#### AdminOrFacultyRequiredMixin
**Before**: Center Head + Faculty only  
**After**: Master Account + Center Head + Faculty

### 2. Student Views Updated (`apps/students/views.py`)

#### StudentListView
- **Master Account**: See all students across all centers
- **Center Head**: See students in their center only

#### StudentDetailView
- **Master Account**: View any student
- **Center Head**: View students in their center
- **Faculty**: View students they teach (have active assignments with)

**Key Changes**:
- Removed strict `CenterHeadRequiredMixin` from detail view
- Added custom permission logic based on role
- Proper queryset filtering per role

### 3. Student Reports Updated (`apps/reports/views.py`)

#### StudentReportView
- **Master Account**: View any student report
- **Center Head**: View reports for students in their center
- **Faculty**: View reports for students they teach

**Key Changes**:
- Removed `AdminOrFacultyRequiredMixin` dependency
- Added custom dispatch with role-based checks
- Faculty permission check: Must have active assignment with student

## Access Matrix

| View/Resource | Master Account | Center Head | Faculty |
|---------------|----------------|-------------|---------|
| Student List | ✅ All students | ✅ Their center | ❌ |
| Student Detail | ✅ All students | ✅ Their center | ✅ Students they teach |
| Student Report | ✅ All students | ✅ Their center | ✅ Students they teach |
| Student CRUD | ✅ All | ✅ Their center | ❌ |
| Faculty Dashboard | ✅ All | ✅ View only | ✅ Own dashboard |
| Center Dashboard | ✅ All centers | ✅ Their center | ❌ |
| All Centers Report | ✅ | ❌ | ❌ |

## Permission Logic

### Master Account
- **Access**: Everything, everywhere
- **No restrictions**: Can view/edit all centers, students, faculty
- **Use case**: System administrator, multi-center oversight

### Center Head
- **Access**: Their assigned center only
- **Restrictions**: Cannot see other centers' data
- **Use case**: Center management, local administration

### Faculty
- **Access**: Students they teach (via assignments)
- **Restrictions**: Cannot see unassigned students
- **Use case**: Teaching, student progress tracking

## Files Modified

1. **`apps/core/mixins.py`** (3 mixins updated)
   - CenterHeadRequiredMixin
   - FacultyRequiredMixin
   - AdminOrFacultyRequiredMixin

2. **`apps/students/views.py`** (2 views updated)
   - StudentListView
   - StudentDetailView

3. **`apps/reports/views.py`** (1 view updated)
   - StudentReportView

## Testing Checklist

### As Master Account
- [ ] Can access `/students/` (all students)
- [ ] Can access `/students/<id>/` (any student)
- [ ] Can access `/reports/student/<id>/` (any student)
- [ ] Can access `/centers/dashboard/` (all centers)
- [ ] Can access `/faculty/` (all faculty)
- [ ] Can access `/reports/all-centers/`

### As Center Head
- [ ] Can access `/students/` (their center only)
- [ ] Can access `/students/<id>/` (their center only)
- [ ] Can access `/reports/student/<id>/` (their center only)
- [ ] Can access `/centers/dashboard/` (their center)
- [ ] Cannot access other centers' data (403)

### As Faculty
- [ ] Cannot access `/students/` (403)
- [ ] Can access `/students/<id>/` (if they teach that student)
- [ ] Can access `/reports/student/<id>/` (if they teach that student)
- [ ] Cannot access students they don't teach (403)
- [ ] Can access `/attendance/` (mark attendance)
- [ ] Can access `/faculty/dashboard/` (own dashboard)

## Security Maintained

✅ Authentication still required for all views  
✅ Profile validation for Center Heads and Faculty  
✅ Proper queryset filtering based on role  
✅ Soft-deleted records excluded  
✅ Audit trail maintained (created_by, modified_by)  
✅ Permission errors raise PermissionDenied (not silent failures)

## Error Messages

### Before
- Generic 403 Forbidden
- No context on why access denied

### After
- Specific error messages:
  - "You must be a center head or master account to access this page."
  - "You can only view students from your center."
  - "You can only view students you teach."
  - "Your faculty profile is not set up."

## Benefits

1. **Master Account Flexibility**: Can troubleshoot, view reports, manage all centers
2. **Proper Role Separation**: Each role has appropriate access
3. **Better UX**: Clear error messages instead of generic 403
4. **Security**: Still maintains proper access control
5. **Scalability**: Easy to add new roles or permissions

## Future Enhancements

- [ ] Add permission caching for performance
- [ ] Create permission decorator for function-based views
- [ ] Add audit logging for permission denials
- [ ] Create admin interface for permission management
- [ ] Add role-based menu filtering in templates

---

**Status**: ✅ Completed  
**Date**: 2025-11-01  
**Version**: 1.0  
**Impact**: All 403 errors resolved, Master Account has full access
