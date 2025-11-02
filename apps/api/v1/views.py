"""
API views for Disha LMS.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout

from rest_framework import viewsets
from rest_framework.decorators import action

from .serializers import (
    LoginSerializer, LoginResponseSerializer, UserSerializer,
    AttendanceRecordSerializer, TopicSerializer,
    StudentSerializer, AssignmentSerializer,
    FacultySerializer, SubjectSerializer,
    CenterSerializer, CenterHeadSerializer,
    CenterReportSerializer, StudentReportSerializer,
    FacultyReportSerializer, InsightsSerializer
)


class LoginAPIView(APIView):
    """
    API endpoint for user login.
    Returns authentication token and user details.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Login user (for session-based auth)
            login(request, user)
            
            # Prepare response
            response_data = {
                'token': token.key,
                'user': UserSerializer(user).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    Deletes the authentication token.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Delete the user's token
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        # Logout user (for session-based auth)
        logout(request)
        
        return Response(
            {'message': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )


class MeAPIView(APIView):
    """
    API endpoint to get current user's profile.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Attendance API Views

class AttendanceViewSet(APIView):
    """
    API endpoint for attendance records.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List attendance records for the authenticated user."""
        from apps.attendance.models import AttendanceRecord
        
        if request.user.is_faculty_member:
            # Faculty sees their own marked attendance
            queryset = AttendanceRecord.objects.filter(
                marked_by=request.user
            ).select_related('student', 'assignment__subject').prefetch_related('topics_covered')
        else:
            # Other roles see all attendance (admin)
            queryset = AttendanceRecord.objects.all().select_related(
                'student', 'assignment__subject'
            ).prefetch_related('topics_covered')
        
        # Filter by date if provided
        date = request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        queryset = queryset.order_by('-date', '-in_time')[:50]  # Limit to 50 records
        
        serializer = AttendanceRecordSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new attendance record."""
        serializer = AttendanceRecordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Set marked_by to current user
            serializer.save(marked_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TodayAttendanceAPIView(APIView):
    """
    API endpoint for today's attendance.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get today's attendance for the authenticated user."""
        from apps.attendance.services import get_today_attendance_for_faculty
        from django.utils import timezone
        
        if not request.user.is_faculty_member:
            return Response(
                {'error': 'Only faculty can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        faculty = request.user.faculty_profile
        attendance_records = get_today_attendance_for_faculty(faculty)
        
        serializer = AttendanceRecordSerializer(attendance_records, many=True)
        return Response({
            'date': timezone.now().date(),
            'count': attendance_records.count(),
            'records': serializer.data
        })


class BulkAttendanceAPIView(APIView):
    """
    API endpoint for bulk attendance marking.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create multiple attendance records at once."""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of attendance records'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_records = []
        errors = []
        
        for i, record_data in enumerate(request.data):
            serializer = AttendanceRecordSerializer(data=record_data)
            
            if serializer.is_valid():
                serializer.save(marked_by=request.user)
                created_records.append(serializer.data)
            else:
                errors.append({
                    'index': i,
                    'errors': serializer.errors
                })
        
        return Response({
            'created': len(created_records),
            'failed': len(errors),
            'records': created_records,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_records else status.HTTP_400_BAD_REQUEST)


# Student Management API ViewSets (T102)

class StudentViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Student CRUD operations.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.students.models import Student
        
        # Center heads see only their center's students
        if hasattr(self.request.user, 'center_head_profile'):
            return Student.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('center')
        
        # Master accounts see all students
        if self.request.user.is_master_account:
            return Student.objects.filter(
                deleted_at__isnull=True
            ).select_related('center')
        
        # Faculty see students assigned to them
        if hasattr(self.request.user, 'faculty_profile'):
            from apps.subjects.models import Assignment
            student_ids = Assignment.objects.filter(
                faculty=self.request.user.faculty_profile,
                is_active=True
            ).values_list('student_id', flat=True)
            return Student.objects.filter(
                id__in=student_ids,
                deleted_at__isnull=True
            ).select_related('center')
        
        return Student.objects.none()
    
    @action(detail=False, methods=['get'])
    def ready_for_transfer(self, request):
        """Get students ready for transfer (completed status)."""
        queryset = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Faculty Management API ViewSet (T103)

class FacultyViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Faculty CRUD operations.
    """
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.faculty.models import Faculty
        
        # Center heads see only their center's faculty
        if hasattr(self.request.user, 'center_head_profile'):
            return Faculty.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('user', 'center')
        
        # Master accounts see all faculty
        if self.request.user.is_master_account:
            return Faculty.objects.filter(
                deleted_at__isnull=True
            ).select_related('user', 'center')
        
        return Faculty.objects.none()


# Subject Management API ViewSet (T104)

class SubjectViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Subject CRUD operations.
    """
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.subjects.models import Subject
        from django.db.models import Count
        
        # Center heads see only their center's subjects
        if hasattr(self.request.user, 'center_head_profile'):
            return Subject.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('center').annotate(
                topic_count=Count('topics')
            )
        
        # Master accounts see all subjects
        if self.request.user.is_master_account:
            return Subject.objects.filter(
                deleted_at__isnull=True
            ).select_related('center').annotate(
                topic_count=Count('topics')
            )
        
        # Faculty see subjects they teach
        if hasattr(self.request.user, 'faculty_profile'):
            from apps.subjects.models import Assignment
            subject_ids = Assignment.objects.filter(
                faculty=self.request.user.faculty_profile,
                is_active=True
            ).values_list('subject_id', flat=True)
            return Subject.objects.filter(
                id__in=subject_ids,
                deleted_at__isnull=True
            ).select_related('center').annotate(
                topic_count=Count('topics')
            )
        
        return Subject.objects.none()
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """Get topics for a specific subject."""
        subject = self.get_object()
        from apps.subjects.models import Topic
        topics = Topic.objects.filter(
            subject=subject,
            is_active=True
        ).order_by('sequence_number')
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


# Assignment API ViewSet (T105)

class AssignmentViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Assignment CRUD operations.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.subjects.models import Assignment
        
        # Center heads see assignments in their center
        if hasattr(self.request.user, 'center_head_profile'):
            return Assignment.objects.filter(
                student__center=self.request.user.center_head_profile.center
            ).select_related('student', 'subject', 'faculty__user')
        
        # Master accounts see all assignments
        if self.request.user.is_master_account:
            return Assignment.objects.all().select_related(
                'student', 'subject', 'faculty__user'
            )
        
        # Faculty see their own assignments
        if hasattr(self.request.user, 'faculty_profile'):
            return Assignment.objects.filter(
                faculty=self.request.user.faculty_profile
            ).select_related('student', 'subject', 'faculty__user')
        
        return Assignment.objects.none()
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Get assignments for a specific student."""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(student_id=student_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_faculty(self, request):
        """Get assignments for a specific faculty."""
        faculty_id = request.query_params.get('faculty_id')
        if not faculty_id:
            return Response(
                {'error': 'faculty_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(faculty_id=faculty_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Multi-Center Management API ViewSets (T129-T130)

class CenterViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Center CRUD operations.
    Master accounts only.
    """
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.centers.models import Center
        from django.db.models import Count, Q
        
        # Only master accounts can access centers API
        if not self.request.user.is_master_account:
            return Center.objects.none()
        
        return Center.objects.filter(
            deleted_at__isnull=True
        ).annotate(
            student_count=Count('students', filter=Q(students__deleted_at__isnull=True)),
            faculty_count=Count('faculty_members', filter=Q(faculty_members__deleted_at__isnull=True)),
            subject_count=Count('subjects', filter=Q(subjects__deleted_at__isnull=True))
        ).order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get detailed statistics for a center."""
        center = self.get_object()
        
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        from apps.subjects.models import Subject
        from apps.attendance.models import AttendanceRecord
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'center': CenterSerializer(center).data,
            'students': {
                'total': Student.objects.filter(center=center, deleted_at__isnull=True).count(),
                'active': Student.objects.filter(center=center, status='active', deleted_at__isnull=True).count(),
                'inactive': Student.objects.filter(center=center, status='inactive', deleted_at__isnull=True).count(),
                'completed': Student.objects.filter(center=center, status='completed', deleted_at__isnull=True).count(),
            },
            'faculty': {
                'total': Faculty.objects.filter(center=center, deleted_at__isnull=True).count(),
                'active': Faculty.objects.filter(center=center, is_active=True, deleted_at__isnull=True).count(),
            },
            'subjects': {
                'total': Subject.objects.filter(center=center, deleted_at__isnull=True).count(),
                'active': Subject.objects.filter(center=center, is_active=True, deleted_at__isnull=True).count(),
            },
            'attendance': {
                'this_week': AttendanceRecord.objects.filter(
                    student__center=center,
                    date__gte=week_ago
                ).count(),
                'this_month': AttendanceRecord.objects.filter(
                    student__center=center,
                    date__gte=month_ago
                ).count(),
            }
        }
        
        return Response(stats)


class CenterHeadViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for CenterHead CRUD operations.
    Master accounts only.
    """
    serializer_class = CenterHeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.centers.models import CenterHead
        
        # Only master accounts can access center heads API
        if not self.request.user.is_master_account:
            return CenterHead.objects.none()
        
        return CenterHead.objects.filter(
            deleted_at__isnull=True
        ).select_related('user', 'center').order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_center(self, request):
        """Get center heads for a specific center."""
        center_id = request.query_params.get('center_id')
        if not center_id:
            return Response(
                {'error': 'center_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(center_id=center_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Report API Views (T150-T153)

class CenterReportAPIView(APIView):
    """
    T150: API endpoint for center report data.
    Returns comprehensive metrics, charts, and insights for a center.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, center_id):
        """Get center report data."""
        from apps.centers.models import Center
        from apps.reports.services import calculate_center_metrics, get_insights_summary
        from django.shortcuts import get_object_or_404
        
        center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        
        # Check permissions
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile') or \
               request.user.center_head_profile.center != center:
                return Response(
                    {'error': 'You do not have permission to view this center.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not request.user.is_master_account:
            return Response(
                {'error': 'You do not have permission to access reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get center metrics
        metrics = calculate_center_metrics(center)[0]
        
        # Get insights
        insights = get_insights_summary(center)
        metrics['insights'] = insights
        
        serializer = CenterReportSerializer(metrics)
        return Response(serializer.data)


class StudentReportAPIView(APIView):
    """
    T151: API endpoint for student report data.
    Returns attendance velocity, learning velocity, and subject progress.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, student_id):
        """Get student report data."""
        from apps.students.models import Student
        from apps.reports.services import (
            calculate_attendance_velocity,
            calculate_learning_velocity,
            prepare_subject_completion_data
        )
        from apps.attendance.models import AttendanceRecord
        from django.shortcuts import get_object_or_404
        
        student = get_object_or_404(Student, pk=student_id, deleted_at__isnull=True)
        
        # Check permissions
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile') or \
               request.user.center_head_profile.center != student.center:
                return Response(
                    {'error': 'You do not have permission to view this student.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not (request.user.is_master_account or request.user.is_faculty_member):
            return Response(
                {'error': 'You do not have permission to access reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get days parameter (default 30)
        days = int(request.query_params.get('days', 30))
        
        # Calculate velocities
        attendance_velocity = calculate_attendance_velocity(student, days=days)
        learning_velocity = calculate_learning_velocity(student)
        
        # Get subject completion data
        subject_completion = prepare_subject_completion_data(student)
        
        # Get recent attendance records
        recent_attendance = AttendanceRecord.objects.filter(
            student=student
        ).select_related('assignment__subject', 'marked_by').order_by('-date')[:10]
        
        # Prepare response data
        data = {
            'student': StudentSerializer(student).data,
            'attendance_velocity': attendance_velocity,
            'learning_velocity': learning_velocity,
            'subject_completion': subject_completion,
            'recent_attendance': AttendanceRecordSerializer(recent_attendance, many=True).data
        }
        
        serializer = StudentReportSerializer(data)
        return Response(serializer.data)


class FacultyReportAPIView(APIView):
    """
    T152: API endpoint for faculty report data.
    Returns teaching statistics, student performance, and session metrics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, faculty_id):
        """Get faculty report data."""
        from apps.faculty.models import Faculty
        from apps.attendance.models import AttendanceRecord
        from apps.subjects.models import Assignment
        from apps.students.models import Student
        from django.shortcuts import get_object_or_404
        from django.db.models import Avg, Sum, Count, Q
        
        faculty = get_object_or_404(Faculty, pk=faculty_id, deleted_at__isnull=True)
        
        # Check permissions
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile') or \
               request.user.center_head_profile.center != faculty.center:
                return Response(
                    {'error': 'You do not have permission to view this faculty.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not request.user.is_master_account:
            return Response(
                {'error': 'You do not have permission to access reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get teaching statistics
        records = AttendanceRecord.objects.filter(marked_by=faculty.user)
        
        stats = {
            'total_sessions': records.count(),
            'total_students': records.values('student').distinct().count(),
            'total_subjects': Assignment.objects.filter(
                faculty=faculty,
                deleted_at__isnull=True
            ).values('subject').distinct().count(),
            'avg_session_duration': records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
            'total_teaching_hours': (records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60,
        }
        
        # Get top students
        top_students = Student.objects.filter(
            id__in=records.values_list('student_id', flat=True).distinct()
        ).annotate(
            session_count=Count('attendancerecord', filter=Q(attendancerecord__marked_by=faculty.user))
        ).order_by('-session_count')[:10]
        
        # Get recent sessions
        recent_sessions = records.select_related('student', 'assignment__subject').order_by('-date')[:10]
        
        # Prepare response data
        data = {
            'faculty': FacultySerializer(faculty).data,
            'stats': stats,
            'top_students': StudentSerializer(top_students, many=True).data,
            'recent_sessions': AttendanceRecordSerializer(recent_sessions, many=True).data
        }
        
        serializer = FacultyReportSerializer(data)
        return Response(serializer.data)


class InsightsAPIView(APIView):
    """
    T153: API endpoint for insights data.
    Returns at-risk students, extended students, and students nearing completion.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, center_id=None):
        """Get insights data."""
        from apps.centers.models import Center
        from apps.reports.services import (
            get_insights_summary,
            get_at_risk_students,
            get_extended_students,
            get_nearing_completion_students
        )
        from django.shortcuts import get_object_or_404
        
        # Determine center
        center = None
        if request.user.is_center_head:
            if hasattr(request.user, 'center_head_profile'):
                center = request.user.center_head_profile.center
        elif request.user.is_master_account:
            if center_id:
                center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        else:
            return Response(
                {'error': 'You do not have permission to access insights.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get query parameters
        days_threshold = int(request.query_params.get('days_threshold', 7))
        months_threshold = int(request.query_params.get('months_threshold', 6))
        completion_threshold = int(request.query_params.get('completion_threshold', 80))
        
        # Get insights
        insights = get_insights_summary(center)
        at_risk = get_at_risk_students(center, days_threshold=days_threshold)
        extended = get_extended_students(center, months_threshold=months_threshold)
        nearing_completion = get_nearing_completion_students(center, completion_threshold=completion_threshold)
        
        # Prepare response data
        data = {
            'at_risk_count': insights['at_risk_count'],
            'extended_count': insights['extended_count'],
            'nearing_completion_count': insights['nearing_completion_count'],
            'at_risk_students': StudentSerializer(at_risk, many=True).data,
            'extended_students': StudentSerializer(extended, many=True).data,
            'nearing_completion': StudentSerializer(nearing_completion, many=True).data
        }
        
        serializer = InsightsSerializer(data)
        return Response(serializer.data)


# Feedback/Survey API Views (T185-T188)

class SurveyViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for survey management.
    
    list: Get all surveys (filtered by role)
    create: Create a new survey
    retrieve: Get survey details
    update: Update a survey
    partial_update: Partially update a survey
    destroy: Soft delete a survey
    
    Permissions:
    - Master Account: Full access to all surveys
    - Center Head: Access to global and their center's surveys
    - Faculty: No access
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get surveys based on user role."""
        from apps.feedback.models import FeedbackSurvey
        from django.db.models import Q, Count, Avg
        
        user = self.request.user
        
        if user.is_master_account:
            queryset = FeedbackSurvey.objects.filter(deleted_at__isnull=True)
        elif user.is_center_head:
            center = user.center_head_profile.center
            queryset = FeedbackSurvey.objects.filter(
                Q(center__isnull=True) | Q(center=center),
                deleted_at__isnull=True
            )
        else:
            queryset = FeedbackSurvey.objects.none()
        
        # Annotate with statistics
        queryset = queryset.annotate(
            response_count=Count('responses'),
            completed_count=Count('responses', filter=Q(responses__is_completed=True)),
            avg_satisfaction=Avg('responses__satisfaction_score', 
                               filter=Q(responses__is_completed=True))
        )
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'published':
            queryset = queryset.filter(is_published=True)
        elif status == 'draft':
            queryset = queryset.filter(is_published=False)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        from .serializers import SurveySerializer, SurveyListSerializer
        if self.action == 'list':
            return SurveyListSerializer
        return SurveySerializer
    
    def perform_create(self, serializer):
        """Create survey with center association."""
        if self.request.user.is_center_head:
            serializer.save(center=self.request.user.center_head_profile.center)
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        """Soft delete survey."""
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save()
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a survey."""
        survey = self.get_object()
        survey.is_published = True
        survey.save()
        serializer = self.get_serializer(survey)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a survey."""
        survey = self.get_object()
        survey.is_published = False
        survey.save()
        serializer = self.get_serializer(survey)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get list of students for sending survey."""
        from apps.students.models import Student
        from .serializers import StudentSerializer
        
        survey = self.get_object()
        
        # Get center
        if request.user.is_center_head:
            center = request.user.center_head_profile.center
        else:
            center = survey.center
        
        if not center:
            return Response(
                {'error': 'No center associated with this survey.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active students
        students = Student.objects.filter(
            center=center,
            deleted_at__isnull=True,
            status='active'
        ).order_by('first_name', 'last_name')
        
        # Get existing responses
        from apps.feedback.models import FeedbackResponse
        existing_ids = FeedbackResponse.objects.filter(
            survey=survey
        ).values_list('student_id', flat=True)
        
        serializer = StudentSerializer(students, many=True)
        return Response({
            'students': serializer.data,
            'existing_response_ids': list(existing_ids)
        })


class SendSurveyAPIView(APIView):
    """
    Send survey emails to selected students.
    
    POST /api/v1/surveys/{id}/send/
    
    Request body:
    {
        "student_ids": [1, 2, 3]
    }
    
    Permissions: Center Head, Master Account
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Send survey to selected students."""
        from apps.feedback.models import FeedbackSurvey
        from apps.feedback.tasks import send_bulk_survey_emails
        from django.shortcuts import get_object_or_404
        from .serializers import SendSurveyRequestSerializer
        
        # Check permissions
        if not (request.user.is_center_head or request.user.is_master_account):
            return Response(
                {'error': 'Only center heads and master accounts can send surveys.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request
        serializer = SendSurveyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get survey
        survey = get_object_or_404(FeedbackSurvey, pk=pk, deleted_at__isnull=True)
        
        # Validate survey is published and active
        if not survey.is_published or not survey.is_active:
            return Response(
                {'error': 'Survey must be published and active to send.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student_ids = serializer.validated_data['student_ids']
        
        # Send emails asynchronously
        try:
            send_bulk_survey_emails.delay(survey.id, student_ids)
            return Response({
                'status': 'success',
                'message': f'Survey emails are being sent to {len(student_ids)} student(s).',
                'survey_id': survey.id,
                'student_count': len(student_ids)
            })
        except Exception as e:
            return Response(
                {'error': f'Error sending surveys: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubmitSurveyAPIView(APIView):
    """
    Public API endpoint for students to submit survey responses.
    No authentication required (uses token).
    
    GET /api/v1/surveys/submit/{token}/
    - Get survey details and questions
    
    POST /api/v1/surveys/submit/{token}/
    - Submit survey responses
    
    Request body:
    {
        "answers": {"question_1": "answer", "question_2": "answer"},
        "satisfaction_score": 5
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        """Get survey details by token."""
        from apps.feedback.models import FeedbackResponse
        from django.shortcuts import get_object_or_404
        from .serializers import SurveySerializer
        
        # Get response by token
        response = get_object_or_404(
            FeedbackResponse,
            token=token,
            deleted_at__isnull=True
        )
        
        # Check if already completed
        if response.is_completed:
            return Response({
                'status': 'completed',
                'message': 'This survey has already been completed.',
                'submitted_at': response.submitted_at
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if survey is valid
        if not response.survey.is_valid():
            return Response({
                'status': 'expired',
                'message': 'This survey has expired.',
                'valid_until': response.survey.valid_until
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Track email opened
        if not response.email_opened_at:
            from django.utils import timezone
            response.email_opened_at = timezone.now()
            response.save(update_fields=['email_opened_at'])
        
        # Return survey and response data
        return Response({
            'survey': SurveySerializer(response.survey).data,
            'response_id': response.id,
            'student_name': response.student.get_full_name(),
            'student_email': response.student.email,
            'is_completed': response.is_completed,
            'email_sent_at': response.email_sent_at
        })
    
    def post(self, request, token):
        """Submit survey responses."""
        from apps.feedback.models import FeedbackResponse
        from django.shortcuts import get_object_or_404
        from .serializers import SubmitSurveyRequestSerializer
        
        # Validate request
        serializer = SubmitSurveyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get response by token
        response = get_object_or_404(
            FeedbackResponse,
            token=token,
            deleted_at__isnull=True
        )
        
        # Validate survey is still valid
        if not response.survey.is_valid():
            return Response({
                'status': 'error',
                'message': 'This survey has expired.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already completed
        if response.is_completed:
            return Response({
                'status': 'error',
                'message': 'This survey has already been completed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save response
        response.answers = serializer.validated_data['answers']
        if 'satisfaction_score' in serializer.validated_data:
            response.satisfaction_score = serializer.validated_data['satisfaction_score']
        response.mark_completed()
        
        # Update student satisfaction score asynchronously
        from apps.feedback.tasks import update_student_satisfaction_scores
        update_student_satisfaction_scores.delay()
        
        return Response({
            'status': 'success',
            'message': 'Survey submitted successfully.',
            'response_id': response.id,
            'submitted_at': response.submitted_at,
            'satisfaction_score': response.satisfaction_score
        })


class SurveyResponsesAPIView(APIView):
    """
    Get survey responses and analytics.
    
    GET /api/v1/surveys/{id}/responses/
    
    Query parameters:
    - limit: Number of responses to return (default: 50)
    - include_pending: Include pending responses (default: false)
    
    Permissions: Center Head, Master Account
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get responses for a survey."""
        from apps.feedback.models import FeedbackSurvey, FeedbackResponse
        from django.shortcuts import get_object_or_404
        from django.db.models import Avg, Q
        from .serializers import ResponseSerializer, SurveyResponseStatsSerializer
        
        # Check permissions
        if not (request.user.is_center_head or request.user.is_master_account):
            return Response(
                {'error': 'Only center heads and master accounts can view responses.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get survey
        if request.user.is_center_head:
            center = request.user.center_head_profile.center
            survey = get_object_or_404(
                FeedbackSurvey,
                pk=pk,
                deleted_at__isnull=True
            )
            # Verify access
            if survey.center and survey.center != center:
                return Response(
                    {'error': 'You do not have permission to view this survey.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            survey = get_object_or_404(FeedbackSurvey, pk=pk, deleted_at__isnull=True)
        
        # Get all responses
        responses = FeedbackResponse.objects.filter(
            survey=survey,
            deleted_at__isnull=True
        ).select_related('student', 'student__center')
        
        # Calculate statistics
        total_responses = responses.count()
        completed_responses = responses.filter(is_completed=True).count()
        pending_responses = responses.filter(is_completed=False).count()
        
        # Average satisfaction score
        completed = responses.filter(is_completed=True, satisfaction_score__isnull=False)
        avg_satisfaction = completed.aggregate(avg=Avg('satisfaction_score'))['avg']
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            count = completed.filter(satisfaction_score=i).count()
            rating_distribution[str(i)] = count
        
        # Get query parameters
        limit = int(request.query_params.get('limit', 50))
        include_pending = request.query_params.get('include_pending', 'false').lower() == 'true'
        
        # Filter responses
        if include_pending:
            response_list = responses.order_by('-created_at')[:limit]
        else:
            response_list = responses.filter(is_completed=True).order_by('-submitted_at')[:limit]
        
        # Serialize responses
        response_data = ResponseSerializer(response_list, many=True).data
        
        return Response({
            'survey_id': survey.id,
            'survey_title': survey.title,
            'total_responses': total_responses,
            'completed_responses': completed_responses,
            'pending_responses': pending_responses,
            'completion_rate': round((completed_responses / total_responses * 100), 2) if total_responses > 0 else 0,
            'avg_satisfaction': round(avg_satisfaction, 2) if avg_satisfaction else None,
            'rating_distribution': rating_distribution,
            'responses': response_data
        })


class SatisfactionTrendsAPIView(APIView):
    """
    Get satisfaction trends over time.
    
    GET /api/v1/feedback/trends/
    
    Query parameters:
    - center_id: Filter by center (optional for master)
    - months: Number of months (default: 6)
    
    Permissions: Center Head, Master Account
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get satisfaction trends."""
        from apps.feedback.services import calculate_satisfaction_trends
        from .serializers import SatisfactionTrendsSerializer
        
        # Check permissions
        if not (request.user.is_center_head or request.user.is_master_account):
            return Response(
                {'error': 'Only center heads and master accounts can view trends.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get center
        center_id = request.query_params.get('center_id')
        if request.user.is_center_head:
            center = request.user.center_head_profile.center
        elif center_id:
            from apps.centers.models import Center
            center = Center.objects.get(id=center_id)
        else:
            center = None
        
        # Get months parameter
        months = int(request.query_params.get('months', 6))
        
        # Calculate trends
        trends_data = calculate_satisfaction_trends(center, months)
        
        return Response({
            'center_id': center.id if center else None,
            'center_name': center.name if center else 'All Centers',
            'months': months,
            'overall_avg': round(trends_data['overall_avg'], 2) if trends_data['overall_avg'] else None,
            'total_responses': trends_data['total_responses'],
            'monthly_trends': trends_data['monthly_trends']
        })


class FacultyBreakdownAPIView(APIView):
    """
    Get faculty satisfaction breakdown.
    
    GET /api/v1/feedback/faculty-breakdown/
    
    Query parameters:
    - center_id: Filter by center (required for master, auto for center head)
    
    Permissions: Center Head, Master Account
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get faculty breakdown."""
        from apps.feedback.services import get_faculty_satisfaction_breakdown
        from .serializers import FacultyBreakdownSerializer
        
        # Check permissions
        if not (request.user.is_center_head or request.user.is_master_account):
            return Response(
                {'error': 'Only center heads and master accounts can view breakdown.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get center
        if request.user.is_center_head:
            center = request.user.center_head_profile.center
        else:
            center_id = request.query_params.get('center_id')
            if not center_id:
                return Response(
                    {'error': 'center_id is required for master accounts.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            from apps.centers.models import Center
            center = Center.objects.get(id=center_id)
        
        # Get breakdown
        breakdown = get_faculty_satisfaction_breakdown(center)
        
        return Response({
            'center_id': center.id,
            'center_name': center.name,
            'faculty_count': len(breakdown),
            'breakdown': breakdown
        })
