"""
Forms for feedback and survey management.
"""

from django import forms
from .models import FeedbackSurvey


class SurveyForm(forms.ModelForm):
    """Form for creating/editing surveys."""
    
    class Meta:
        model = FeedbackSurvey
        fields = ['title', 'description', 'center', 'questions', 'valid_from', 'valid_until', 'is_active', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
            'center': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'questions': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full font-mono', 
                'rows': 10,
                'placeholder': '[\n  {\n    "id": 1,\n    "text": "How satisfied are you with your learning experience?",\n    "type": "rating",\n    "required": true\n  }\n]'
            }),
            'valid_from': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
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
