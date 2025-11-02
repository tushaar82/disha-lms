# How to Set Up a Center Head Profile

## The Error You're Seeing

```
RelatedObjectDoesNotExist at /students/
User has no center_head_profile.
```

This happens because your user account doesn't have a **CenterHead profile** linked to it. The student management system requires users to have this profile to know which center they manage.

---

## Solution: Create a Center Head Profile

### Step 1: Access Admin Panel

1. Go to: http://127.0.0.1:8000/admin/
2. Login with your superuser credentials

### Step 2: Create or Update User

**Option A: Create a New Center Head User**

1. Go to **Users** → **Add User**
2. Fill in:
   - Email: `centerhead@example.com`
   - Password: (set a password)
   - First Name: `John`
   - Last Name: `Doe`
   - **Role**: Select **`center_head`** (IMPORTANT!)
   - Is Active: ✓ Checked
3. Click **Save**

**Option B: Update Existing User**

1. Go to **Users** → Find your user
2. Edit the user
3. Change **Role** to **`center_head`**
4. Click **Save**

### Step 3: Create Center Head Profile

1. Go to **Center Heads** → **Add Center Head**
2. Fill in:
   - **User**: Select the center head user you just created/updated
   - **Center**: Select your center (e.g., "Mumbai Center")
   - **Employee ID**: `CH001` (or any unique ID)
   - **Joining Date**: Select today's date
   - **Is Active**: ✓ Checked
3. Click **Save**

### Step 4: Test Access

1. **Logout** from admin panel
2. Go to: http://127.0.0.1:8000/accounts/login/
3. Login with the center head credentials
4. Visit: http://127.0.0.1:8000/students/
5. ✅ You should now see the student list page!

---

## Quick Test Data Setup

To fully test the student management system, create this test data in admin:

### 1. Create a Center (if not exists)
- Name: Mumbai Center
- Code: MUM001
- Address, city, state, etc.

### 2. Create Center Head User + Profile
- User with role: center_head
- CenterHead profile linking user to center

### 3. Create Test Students
- Go to **Students** → **Add Student**
- Create 2-3 test students
- Assign them to your center

### 4. Create Test Subjects
- Go to **Subjects** → **Add Subject**
- Create subjects like "Python Programming", "Data Science"

### 5. Create Test Faculty
- Create faculty user (role: faculty)
- Create Faculty profile
- Assign subjects to faculty

### 6. Create Assignments
- Link students to subjects and faculty

---

## Understanding the User Roles

### Master Account (`master`)
- Can manage multiple centers
- Can switch between centers
- Full system access

### Center Head (`center_head`)
- Manages ONE center
- Can manage students, faculty, subjects in their center
- Cannot access other centers

### Faculty (`faculty`)
- Can mark attendance
- Can view their assigned students
- Limited management access

---

## Troubleshooting

### Error: "You must be a center head to access this page"
**Solution**: Change user's role to `center_head` in admin

### Error: "Your center head profile is not set up"
**Solution**: Create a CenterHead profile in admin linking the user to a center

### Error: "No students found"
**Solution**: Create test students in admin and assign them to your center

### Can't see admin panel
**Solution**: Make sure you're logged in as a superuser or staff user

---

## What You Can Do After Setup

Once your center head profile is set up, you can:

✅ **View Students**: http://127.0.0.1:8000/students/  
✅ **Add Student**: http://127.0.0.1:8000/students/create/  
✅ **Search Students**: Use the search bar on student list  
✅ **Filter by Status**: Active, Inactive, Completed  

**Note**: Some features (edit, detail, assign) need additional templates which are being implemented.

---

## Next Steps

After setting up your center head profile:

1. ✅ Test student list page
2. ✅ Try creating a student
3. ⏳ Wait for remaining templates (detail, edit, assign)
4. ⏳ Wait for faculty management
5. ⏳ Wait for subject management
6. ⏳ Wait for dashboard

---

## Quick Reference: Admin URLs

- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Users**: http://127.0.0.1:8000/admin/accounts/user/
- **Centers**: http://127.0.0.1:8000/admin/centers/center/
- **Center Heads**: http://127.0.0.1:8000/admin/centers/centerhead/
- **Students**: http://127.0.0.1:8000/admin/students/student/
- **Faculty**: http://127.0.0.1:8000/admin/faculty/faculty/
- **Subjects**: http://127.0.0.1:8000/admin/subjects/subject/

---

**Need Help?** Check the error message carefully - it usually tells you exactly what's missing!
