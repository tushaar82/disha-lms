"""
API serializers for Disha LMS.
"""

from rest_framework import serializers
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'is_active', 
            'date_joined', 'last_login',
            'is_master_account', 'is_center_head', 'is_faculty_member'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class LoginSerializer(serializers.Serializer):
    """Serializer for login requests."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        from django.contrib.auth import authenticate
        
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include "email" and "password".')
        
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""
    
    token = serializers.CharField()
    user = UserSerializer()


# Attendance Serializers

class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic model."""
    
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        from apps.subjects.models import Topic
        model = Topic
        fields = ['id', 'subject', 'subject_name', 'name', 'description', 
                  'sequence_number', 'estimated_duration', 'is_active']
        read_only_fields = ['id']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRecord model."""
    
    from apps.subjects.models import Topic
    
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='assignment.subject.name', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.get_full_name', read_only=True)
    topics_covered = TopicSerializer(many=True, read_only=True)
    topic_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        source='topics_covered',
        required=False,
        queryset=Topic.objects.all()
    )
    
    class Meta:
        from apps.attendance.models import AttendanceRecord
        model = AttendanceRecord
        fields = [
            'id', 'student', 'student_name', 'assignment', 'subject_name',
            'date', 'in_time', 'out_time', 'duration_minutes',
            'topics_covered', 'topic_ids', 'notes',
            'is_backdated', 'backdated_reason',
            'marked_by', 'marked_by_name',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'duration_minutes', 'is_backdated', 'marked_by', 
                            'created_at', 'modified_at']


# Student Management Serializers (T100)

class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    center_name = serializers.CharField(source='center.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        from apps.students.models import Student
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'date_of_birth', 'center', 'center_name', 'enrollment_number',
            'enrollment_date', 'status', 'status_display',
            'guardian_name', 'guardian_phone', 'guardian_email',
            'address', 'city', 'state', 'pincode', 'notes',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model."""
    
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.user.get_full_name', read_only=True)
    
    class Meta:
        from apps.subjects.models import Assignment
        model = Assignment
        fields = [
            'id', 'student', 'student_name', 'subject', 'subject_name',
            'faculty', 'faculty_name', 'start_date', 'end_date', 'is_active',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']


# Faculty Management Serializers (T101)

class FacultySerializer(serializers.ModelSerializer):
    """Serializer for Faculty model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    center_name = serializers.CharField(source='center.name', read_only=True)
    
    class Meta:
        from apps.faculty.models import Faculty
        model = Faculty
        fields = [
            'id', 'user', 'user_email', 'user_name', 'center', 'center_name',
            'employee_id', 'joining_date', 'specialization', 'qualification',
            'experience_years', 'is_active',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model (global subjects, not center-specific)."""
    
    topic_count = serializers.IntegerField(read_only=True, required=False)
    
    class Meta:
        from apps.subjects.models import Subject
        model = Subject
        fields = [
            'id', 'name', 'code', 'description', 'is_active', 'topic_count',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']


# Multi-Center Management Serializers (T128)

class CenterSerializer(serializers.ModelSerializer):
    """Serializer for Center model."""
    
    student_count = serializers.IntegerField(read_only=True)
    faculty_count = serializers.IntegerField(read_only=True)
    subject_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        from apps.centers.models import Center
        model = Center
        fields = [
            'id', 'name', 'code', 'address', 'city', 'state', 'pincode',
            'phone', 'email', 'is_active',
            'student_count', 'faculty_count', 'subject_count',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']


class CenterHeadSerializer(serializers.ModelSerializer):
    """Serializer for CenterHead model."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    center_name = serializers.CharField(source='center.name', read_only=True)
    center_code = serializers.CharField(source='center.code', read_only=True)
    
    class Meta:
        from apps.centers.models import CenterHead
        model = CenterHead
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'center', 'center_name', 'center_code',
            'employee_id', 'joining_date', 'is_active',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']


# Report Serializers (T150-T153)

class CenterReportSerializer(serializers.Serializer):
    """Serializer for center report data."""
    
    center_id = serializers.IntegerField()
    center_name = serializers.CharField()
    center_code = serializers.CharField()
    center_city = serializers.CharField()
    center_state = serializers.CharField()
    students = serializers.DictField()
    faculty = serializers.DictField()
    subjects = serializers.DictField()
    attendance = serializers.DictField()
    insights = serializers.DictField(required=False)


class AttendanceVelocitySerializer(serializers.Serializer):
    """Serializer for attendance velocity metrics."""
    
    sessions_per_week = serializers.FloatField()
    total_sessions = serializers.IntegerField()
    avg_session_duration = serializers.FloatField()
    total_learning_hours = serializers.FloatField()


class LearningVelocitySerializer(serializers.Serializer):
    """Serializer for learning velocity metrics."""
    
    topics_per_session = serializers.FloatField()
    total_topics_covered = serializers.IntegerField()
    minutes_per_topic = serializers.FloatField()
    total_sessions = serializers.IntegerField()


class StudentReportSerializer(serializers.Serializer):
    """Serializer for student report data."""
    
    student = StudentSerializer()
    attendance_velocity = AttendanceVelocitySerializer()
    learning_velocity = LearningVelocitySerializer()
    recent_attendance = AttendanceRecordSerializer(many=True)
    subject_completion = serializers.ListField(child=serializers.DictField())


class FacultyReportSerializer(serializers.Serializer):
    """Serializer for faculty report data."""
    
    faculty = FacultySerializer()
    stats = serializers.DictField()
    top_students = StudentSerializer(many=True)
    recent_sessions = AttendanceRecordSerializer(many=True)


class InsightsSerializer(serializers.Serializer):
    """Serializer for insights data."""
    
    at_risk_count = serializers.IntegerField()
    extended_count = serializers.IntegerField()
    nearing_completion_count = serializers.IntegerField()
    at_risk_students = StudentSerializer(many=True)
    extended_students = StudentSerializer(many=True)
    nearing_completion = StudentSerializer(many=True)


# T184: Feedback/Survey Serializers
class SurveySerializer(serializers.ModelSerializer):
    """
    Serializer for FeedbackSurvey model.
    Provides complete CRUD operations for surveys.
    """
    
    response_count = serializers.IntegerField(read_only=True, required=False)
    is_valid = serializers.SerializerMethodField()
    center_name = serializers.CharField(source='center.name', read_only=True, allow_null=True)
    
    class Meta:
        from apps.feedback.models import FeedbackSurvey
        model = FeedbackSurvey
        fields = [
            'id', 'title', 'description', 'questions', 'center', 'center_name',
            'valid_from', 'valid_until', 'is_active', 'is_published',
            'created_at', 'updated_at', 'is_valid', 'response_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_valid(self, obj):
        """Check if survey is currently valid."""
        return obj.is_valid()


class ResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for FeedbackResponse model.
    Includes nested student and survey data.
    """
    
    student = StudentSerializer(read_only=True)
    survey = SurveySerializer(read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    survey_title = serializers.CharField(source='survey.title', read_only=True)
    
    class Meta:
        from apps.feedback.models import FeedbackResponse
        model = FeedbackResponse
        fields = [
            'id', 'survey', 'survey_id', 'survey_title', 'student', 'student_id', 
            'student_name', 'token', 'answers', 'satisfaction_score',
            'submitted_at', 'is_completed', 'email_sent_at', 'email_opened_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'token', 'submitted_at', 'is_completed', 
            'email_sent_at', 'email_opened_at', 'created_at', 'updated_at'
        ]


class SurveyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for survey lists."""
    
    response_count = serializers.IntegerField(read_only=True)
    completed_count = serializers.IntegerField(read_only=True, required=False)
    avg_satisfaction = serializers.FloatField(read_only=True, required=False)
    center_name = serializers.CharField(source='center.name', read_only=True, allow_null=True)
    
    class Meta:
        from apps.feedback.models import FeedbackSurvey
        model = FeedbackSurvey
        fields = [
            'id', 'title', 'description', 'center', 'center_name',
            'valid_from', 'valid_until', 'is_active', 'is_published',
            'response_count', 'completed_count', 'avg_satisfaction', 'created_at'
        ]


class SendSurveyRequestSerializer(serializers.Serializer):
    """Serializer for send survey request."""
    
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of student IDs to send survey to"
    )


class SubmitSurveyRequestSerializer(serializers.Serializer):
    """Serializer for survey submission request."""
    
    answers = serializers.JSONField(help_text="Survey answers as JSON object")
    satisfaction_score = serializers.IntegerField(
        min_value=1, 
        max_value=5,
        required=False,
        help_text="Overall satisfaction score (1-5)"
    )


class SurveyResponseStatsSerializer(serializers.Serializer):
    """Serializer for survey response statistics."""
    
    survey_id = serializers.IntegerField()
    survey_title = serializers.CharField()
    total_responses = serializers.IntegerField()
    completed_responses = serializers.IntegerField()
    pending_responses = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_satisfaction = serializers.FloatField(allow_null=True)
    rating_distribution = serializers.DictField()
    responses = ResponseSerializer(many=True)


class SatisfactionTrendsSerializer(serializers.Serializer):
    """Serializer for satisfaction trends data."""
    
    month = serializers.CharField()
    avg_satisfaction = serializers.FloatField(allow_null=True)
    response_count = serializers.IntegerField()


class FacultyBreakdownSerializer(serializers.Serializer):
    """Serializer for faculty satisfaction breakdown."""
    
    faculty_id = serializers.IntegerField()
    faculty_name = serializers.CharField()
    response_count = serializers.IntegerField()
    avg_satisfaction = serializers.FloatField()
