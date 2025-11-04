"""
Forms for core app configuration.
"""

from django import forms
from django.core.exceptions import ValidationError
from apps.core.utils import validate_gemini_api_key


class GeminiAPIKeyForm(forms.Form):
    """Form for configuring Gemini API key."""
    
    api_key = forms.CharField(
        label='Gemini API Key',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter your Gemini API key'
        }),
        help_text='Get your API key from Google AI Studio: https://makersuite.google.com/app/apikey'
    )
    
    def clean_api_key(self):
        """Validate the API key."""
        api_key = self.cleaned_data.get('api_key')
        
        if not api_key:
            raise ValidationError('API key is required.')
        
        # Test the API key
        is_valid, message = validate_gemini_api_key(api_key)
        
        if not is_valid:
            raise ValidationError(f'Invalid API key: {message}')
        
        return api_key


class AISettingsForm(forms.Form):
    """Form for configuring AI settings."""
    
    enable_ai_insights = forms.BooleanField(
        label='Enable AI Insights',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text='Enable AI-powered insights across the platform'
    )
    
    enable_forecasting = forms.BooleanField(
        label='Enable Forecasting',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text='Enable predictive analytics and forecasting'
    )
    
    cache_ttl = forms.IntegerField(
        label='Cache Duration (seconds)',
        initial=3600,
        min_value=300,
        max_value=86400,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '3600'
        }),
        help_text='How long to cache AI responses (300-86400 seconds)'
    )
    
    forecast_periods = forms.IntegerField(
        label='Default Forecast Periods',
        initial=30,
        min_value=7,
        max_value=365,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '30'
        }),
        help_text='Default number of periods for forecasts (7-365 days)'
    )
    
    def clean_cache_ttl(self):
        """Validate cache TTL."""
        ttl = self.cleaned_data.get('cache_ttl')
        
        if ttl < 300:
            raise ValidationError('Cache TTL must be at least 300 seconds (5 minutes).')
        
        if ttl > 86400:
            raise ValidationError('Cache TTL cannot exceed 86400 seconds (24 hours).')
        
        return ttl
    
    def clean_forecast_periods(self):
        """Validate forecast periods."""
        periods = self.cleaned_data.get('forecast_periods')
        
        if periods < 7:
            raise ValidationError('Forecast periods must be at least 7 days.')
        
        if periods > 365:
            raise ValidationError('Forecast periods cannot exceed 365 days.')
        
        return periods


class SystemConfigurationForm(forms.Form):
    """Dynamic form for editing system configurations."""
    
    key = forms.CharField(
        label='Configuration Key',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'readonly': 'readonly'
        })
    )
    
    value = forms.CharField(
        label='Value',
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3
        })
    )
    
    description = forms.CharField(
        label='Description',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 2
        }),
        help_text='Human-readable description of this configuration'
    )
    
    is_encrypted = forms.BooleanField(
        label='Encrypt Value',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text='Whether to encrypt this value for security'
    )
