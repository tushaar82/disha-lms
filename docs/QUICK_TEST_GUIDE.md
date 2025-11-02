# Quick Test Guide - Phase 5 Complete!

## 🚀 Start the Server

```bash
cd /home/tushka/Projects/disha_lms/disha-lms
source venv/bin/activate
python manage.py runserver
```

## 🔐 Login Credentials

### Master Account (Full Access)
```
Email: master@example.com
Password: master123
```

### Center Head (Center Management)
```
Email: centerhead@example.com
Password: center123
```

### Faculty (Attendance Tracking)
```
Email: faculty@example.com
Password: faculty123
```

## 📍 Key URLs to Test

### Master Account Features:
1. **Centers List**: http://127.0.0.1:8000/centers/
   - View all centers
   - Create new center
   - Edit/Delete centers
   - Click "Dashboard" to access any center

2. **All Centers Report**: http://127.0.0.1:8000/reports/all-centers/
   - View summary statistics
   - See 4 interactive Google Charts
   - Compare center performance
   - View detailed metrics table

3. **Context Switching**:
   - After accessing a center dashboard, check navbar
   - Click the center name dropdown (top right)
   - Select different center from list
   - Dashboard updates instantly

### Center Head Features:
4. **Dashboard**: http://127.0.0.1:8000/centers/dashboard/
   - View center statistics
   - See attendance trends
   - Quick actions

5. **Students**: http://127.0.0.1:8000/students/
   - Manage students
   - Assign subjects/faculty
   - Ready for transfer view

6. **Faculty**: http://127.0.0.1:8000/faculty/
   - Manage faculty members
   - View statistics

7. **Subjects**: http://127.0.0.1:8000/subjects/
   - Manage subjects
   - Add topics

### Faculty Features:
8. **Today's Attendance**: http://127.0.0.1:8000/attendance/today/
   - View today's records
   - See statistics

9. **Mark Attendance**: http://127.0.0.1:8000/attendance/mark/
   - Mark new attendance
   - Select topics covered

10. **History**: http://127.0.0.1:8000/attendance/history/
    - View all attendance records
    - Filter and search

### API:
11. **API Documentation**: http://127.0.0.1:8000/api/docs/
    - Interactive Swagger UI
    - Test all endpoints

12. **Admin Panel**: http://127.0.0.1:8000/admin/
    - Django admin interface
    - View audit logs

## ✅ What to Verify

### Navbar Links (Fixed!)
- **Master Account**: Should see "Centers" and "Reports" links
- **Center Head**: Should see "Dashboard", "Students", "Faculty", "Subjects"
- **Faculty**: Should see "Today", "Mark", "History"

### Phase 5 Features:
1. ✅ Center CRUD operations work
2. ✅ Center switching via navbar dropdown
3. ✅ All Centers Report loads with charts
4. ✅ Charts are interactive and responsive
5. ✅ Detailed metrics table shows all centers
6. ✅ "View Dashboard" buttons work
7. ✅ Session persists across page refreshes

## 🎯 Test Flow

### Complete Test (5 minutes):

1. **Login as Master Account**
   - Go to http://127.0.0.1:8000/accounts/login/
   - Use master@example.com / master123

2. **View Centers**
   - Should redirect to /centers/ automatically
   - Verify navbar shows "Centers" and "Reports" links

3. **Access a Center Dashboard**
   - Click "Dashboard" button on any center card
   - Verify dashboard loads with that center's data
   - Check navbar - should show center name dropdown

4. **Switch Centers**
   - Click center name dropdown in navbar
   - Select a different center
   - Verify dashboard updates

5. **View Reports**
   - Click "Reports" in navbar
   - Verify summary cards show correct totals
   - Verify 4 charts render properly
   - Scroll to detailed table
   - Click "View Dashboard" on any center

6. **Test API**
   - Go to http://127.0.0.1:8000/api/docs/
   - Click "Authorize" and login
   - Try GET /api/v1/centers/
   - Try GET /api/v1/centers/{id}/statistics/

## 🐛 If Something Doesn't Work

### Navbar Links Not Showing?
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check browser console for errors

### Charts Not Rendering?
- Check internet connection (Google Charts loads from CDN)
- Check browser console for JavaScript errors
- Try different browser

### Center Switching Not Working?
- Check if session middleware is enabled
- Verify you're logged in as master account
- Check browser cookies are enabled

## 📊 Expected Results

### Centers List Page:
- Card-based layout
- Search bar at top
- Filter by status (Active/Inactive)
- Each card shows: name, code, location, statistics
- Buttons: Dashboard, View, Edit

### All Centers Report:
- 5 summary cards at top
- 4 charts in 2x2 grid
- 2 "Top Performers" sections
- Detailed metrics table at bottom
- All data should be real-time

### Navbar:
- Master Account: Centers | Reports | Profile | Admin
- Center Switcher dropdown (when center selected)
- User dropdown on right

## 🎉 Success Indicators

✅ All navbar links visible and working  
✅ Center switching seamless  
✅ Reports page loads with charts  
✅ No console errors  
✅ All buttons functional  
✅ Data displays correctly  

---

**Phase 5 is 100% Complete!** 🎊

Test it now and enjoy the full multi-center management system!
