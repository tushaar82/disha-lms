"""
URL configuration for reports app.
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Master Account Dashboard
    path('master/', views.MasterAccountDashboardView.as_view(), name='master_dashboard'),
    path('master/faculty/', views.MasterFacultyListView.as_view(), name='master_faculty_list'),
    path('master/students/', views.MasterStudentSearchView.as_view(), name='master_student_search'),
    
    # T123: All centers comparison
    path('all-centers/', views.AllCentersReportView.as_view(), name='all_centers'),
    
    # T132: Center report
    path('center/<int:center_id>/', views.CenterReportView.as_view(), name='center_report'),
    
    # T133: Student report
    path('student/<int:student_id>/', views.StudentReportView.as_view(), name='student_report'),
    
    # T134: Faculty report
    path('faculty/<int:faculty_id>/', views.FacultyReportView.as_view(), name='faculty_report'),
    
    # T135: Insights
    path('insights/', views.InsightsView.as_view(), name='insights'),
    path('insights/<int:center_id>/', views.InsightsView.as_view(), name='insights_center'),
    
    # T147, T148: Export views
    path('export/pdf/<str:report_type>/<int:object_id>/', views.ExportReportPDFView.as_view(), name='export_pdf'),
    path('export/csv/<str:report_type>/<int:object_id>/', views.ExportReportCSVView.as_view(), name='export_csv'),
]
