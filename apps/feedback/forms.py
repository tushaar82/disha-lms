"""
Forms for feedback and survey management.
"""

from django import forms
from .models import FeedbackSurvey, FacultyFeedback


class SurveyForm(forms.ModelForm):
    """Form for creating/editing surveys."""
    
    class Meta:
        model = FeedbackSurvey
        fields = ['title', 'description', 'center', 'questions', 'valid_from', 'valid_until', 'is_active', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'center': forms.Select(attrs={'class': 'form-select'}),
            'questions': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full font-mono', 
                'rows': 10,
                'placeholder': '[\n  {\n    "id": 1,\n    "text": "How satisfied are you with your learning experience?",\n    "type": "rating",\n    "required": true\n  }\n]'
            }),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'center': 'Leave blank for global surveys available to all centers',
            'questions': 'Enter survey questions in JSON format',
            'is_published': 'Published surveys can be sent to students',
        }
    
    def clean_questions(self):
        """Validate questions JSON format."""
        import json
        questions = self.cleaned_data.get('questions')
        
        if isinstance(questions, str):
            try:
                questions = json.loads(questions)
            except json.JSONDecodeError:
                raise forms.ValidationError('Invalid JSON format. Please check your syntax.')
        
        if not isinstance(questions, list):
            raise forms.ValidationError('Questions must be a list of question objects.')
        
        # Validate each question has required fields
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                raise forms.ValidationError(f'Question {i+1} must be an object.')
            if 'text' not in question:
                raise forms.ValidationError(f'Question {i+1} is missing "text" field.')
            if 'type' not in question:
                raise forms.ValidationError(f'Question {i+1} is missing "type" field.')
        
        return questions
    
    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        
        if valid_from and valid_until and valid_until < valid_from:
            raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data


class FacultyFeedbackForm(forms.ModelForm):
    """Form for students to submit faculty feedback."""
    
    class Meta:
        model = FacultyFeedback
        fields = [
            'teaching_quality',
            'subject_knowledge',
            'explanation_clarity',
            'student_engagement',
            'doubt_resolution',
            'comments'
        ]
        widgets = {
            'teaching_quality': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'subject_knowledge': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'explanation_clarity': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'student_engagement': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'doubt_resolution': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'comments': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Share any additional feedback or suggestions (optional)'
            }),
        }
        labels = {
            'teaching_quality': 'How would you rate the overall teaching quality?',
            'subject_knowledge': 'How knowledgeable is the faculty about the subject?',
            'explanation_clarity': 'How clear and understandable are the explanations?',
            'student_engagement': 'How well does the faculty engage and motivate you?',
            'doubt_resolution': 'How effectively does the faculty resolve your doubts?',
            'comments': 'Additional Comments (Optional)',
        }
    
    def clean(self):
        """Validate all ratings are provided."""
        cleaned_data = super().clean()
        
        required_fields = [
            'teaching_quality',
            'subject_knowledge',
            'explanation_clarity',
            'student_engagement',
            'doubt_resolution'
        ]
        
        for field in required_fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError(f'Please provide a rating for all questions.')
        
        return cleaned_data
