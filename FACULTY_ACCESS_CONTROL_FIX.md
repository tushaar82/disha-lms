# Faculty Access Control Fix

## Issue
Faculty pages were not accessible to Master Account users due to `CenterHeadRequiredMixin` restriction.

## Solution
Updated all faculty views to support both **Master Account** and **Center Head** access with proper filtering.

---

## Changes Made

### 1. FacultyListView
**Before**: Only Center Heads could access
**After**: Both Master Account and Center Heads can access

**Features**:
- Master Account: Can view ALL faculty across ALL centers
- Master Account: Can filter by specific center using dropdown
- Center Head: Can view only their center's faculty (auto-filtered)

**Access Control**:
```python
def dispatch(self, request, *args, **kwargs):
    if not (request.user.is_master_account or request.user.is_center_head):
        raise PermissionDenied()
    return super().dispatch(request, *args, **kwargs)
```

**Filtering Logic**:
```python
# Master Account: Optional center filter
center_filter = request.GET.get('center')
if center_filter and request.user.is_master_account:
    queryset = queryset.filter(center_id=center_filter)

# Center Head: Auto-filter to their center
if request.user.is_center_head:
    queryset = queryset.filter(center=request.user.center_head_profile.center)
```

---

### 2. FacultyCreateView
**Before**: Only Center Heads could create faculty
**After**: Both Master Account and Center Heads can create faculty

**Features**:
- Master Account: Can create faculty for ANY center
- Center Head: Can create faculty only for their center (readonly)

**Form Handling**:
```python
def get_form(self, form_class=None):
    form = super().get_form(form_class)
    # For center heads, limit to their center
    if self.request.user.is_center_head:
        form.fields['center'].initial = self.request.user.center_head_profile.center
        form.fields['center'].widget.attrs['readonly'] = True
    return form
```

---

### 3. FacultyDetailView
**Before**: Only Center Heads could view faculty details
**After**: Both Master Account and Center Heads can view

**Features**:
- Master Account: Can view ANY faculty's details
- Center Head: Can view only their center's faculty

**Queryset Filtering**:
```python
def get_queryset(self):
    queryset = Faculty.objects.filter(deleted_at__isnull=True)
    
    if self.request.user.is_center_head:
        queryset = queryset.filter(center=self.request.user.center_head_profile.center)
    
    return queryset
```

---

### 4. FacultyUpdateView
**Before**: Only Center Heads could edit faculty
**After**: Both Master Account and Center Heads can edit

**Features**:
- Master Account: Can edit ANY faculty
- Center Head: Can edit only their center's faculty

**Same filtering logic as DetailView**

---

### 5. FacultyDashboardView
**Already Correct**: Uses `AdminOrMasterRequiredMixin`

**Access**: Master Account + Center Head only

---

## Template Updates

### faculty_list.html

**Added Center Filter Dropdown** (Master Account only):
```html
{% if user.is_master_account %}
<div class="form-control">
    <select name="center" class="select select-bordered w-full">
        <option value="">All Centers</option>
        {% for center in centers %}
        <option value="{{ center.id }}">{{ center.name }} ({{ center.code }})</option>
        {% endfor %}
    </select>
</div>
{% endif %}
```

**Added Role-based "Add Faculty" Button**:
```html
{% if user.is_master_account or user.is_center_head %}
<a href="{% url 'faculty:create' %}" class="btn btn-primary">Add Faculty</a>
{% endif %}
```

---

## Access Matrix

| Feature | Master Account | Center Head | Faculty |
|---------|---------------|-------------|---------|
| **List Faculty** | ✅ All centers | ✅ Own center | ❌ |
| **Filter by Center** | ✅ Yes | ❌ Auto-filtered | ❌ |
| **View Faculty Detail** | ✅ Any faculty | ✅ Own center | ❌ |
| **Create Faculty** | ✅ Any center | ✅ Own center | ❌ |
| **Edit Faculty** | ✅ Any faculty | ✅ Own center | ❌ |
| **Faculty Dashboard** | ✅ Any faculty | ✅ Any faculty | ❌ |

---

## URLs

| URL | Access | Description |
|-----|--------|-------------|
| `/faculty/` | Master + Admin | List all faculty |
| `/faculty/?center=5` | Master only | Filter by center |
| `/faculty/create/` | Master + Admin | Create new faculty |
| `/faculty/12/` | Master + Admin | View faculty details |
| `/faculty/12/edit/` | Master + Admin | Edit faculty |
| `/faculty/dashboard/` | Master + Admin | Faculty performance overview |
| `/faculty/dashboard/12/` | Master + Admin | Specific faculty performance |

---

## Files Modified

1. **apps/faculty/views.py**
   - Updated `FacultyListView` - Added Master support + center filter
   - Updated `FacultyCreateView` - Removed CenterHeadRequiredMixin
   - Updated `FacultyDetailView` - Removed CenterHeadRequiredMixin
   - Updated `FacultyUpdateView` - Removed CenterHeadRequiredMixin
   - All views now have custom `dispatch()` with proper access control

2. **apps/faculty/templates/faculty/faculty_list.html**
   - Added center filter dropdown (Master only)
   - Added role-based "Add Faculty" button visibility
   - Responsive grid (4 columns for Master, 3 for Admin)

---

## Testing Checklist

### As Master Account:
- [ ] Can access `/faculty/`
- [ ] Can see "All Centers" dropdown
- [ ] Can filter by specific center
- [ ] Can see faculty from all centers (when no filter)
- [ ] Can see faculty from specific center (when filtered)
- [ ] Can click "Add Faculty" button
- [ ] Can create faculty for any center
- [ ] Can view any faculty's details
- [ ] Can edit any faculty
- [ ] Can access faculty dashboard

### As Center Head:
- [ ] Can access `/faculty/`
- [ ] Cannot see center filter dropdown
- [ ] Can see only their center's faculty
- [ ] Can click "Add Faculty" button
- [ ] Can create faculty (center is readonly)
- [ ] Can view their center's faculty details
- [ ] Can edit their center's faculty
- [ ] Can access faculty dashboard

### As Faculty:
- [ ] Cannot access `/faculty/` (403 error)
- [ ] Cannot access faculty dashboard (403 error)

---

## Migration Notes

**No database migrations required** - Only view and template changes.

---

## Rollback Plan

If issues occur, revert these files:
1. `apps/faculty/views.py`
2. `apps/faculty/templates/faculty/faculty_list.html`

---

## Status

✅ **COMPLETED** - All faculty pages now accessible to Master Account and Center Head with proper filtering.

---

**Date**: 2025-11-01  
**Version**: 1.0  
**Author**: Cascade AI
