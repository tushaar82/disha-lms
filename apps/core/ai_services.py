"""
AI Services module for Gemini API integration.
Provides AI-powered insights, forecasting, and recommendations.
"""

import logging
import json
from django.core.cache import cache
from django.conf import settings
from apps.core.models import SystemConfiguration
from apps.core.utils import format_ai_response, sanitize_data_for_ai
from apps.core.decorators import retry_on_failure, measure_performance

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for interacting with Google's Gemini API.
    Provides methods for generating insights, forecasts, and recommendations.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Optional API key (uses SystemConfiguration if not provided)
        """
        if api_key is None:
            api_key = SystemConfiguration.get_config('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("Gemini API key not configured")
        
        self.api_key = api_key
        self._client = None
        self._model = None
    
    def _get_client(self):
        """Get or create Gemini client instance."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
                self._model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {str(e)}")
                raise
        
        return self._client
    
    def _get_model(self):
        """Get Gemini model instance."""
        if self._model is None:
            self._get_client()
        return self._model
    
    @retry_on_failure(max_retries=3, delay=2)
    def test_connection(self):
        """
        Test API connectivity.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            client = self._get_client()
            models = list(client.list_models())
            return True, f"Connection successful. {len(models)} models available."
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, f"Connection failed: {str(e)}"
    
    @measure_performance
    @retry_on_failure(max_retries=2, delay=1)
    def generate_insights(self, data, context=""):
        """
        Generate AI insights from data.
        
        Args:
            data: Data dictionary to analyze
            context: Additional context for the analysis
            
        Returns:
            dict: Insights with text, confidence, and metadata
        """
        try:
            model = self._get_model()
            
            # Sanitize data before sending to AI
            sanitized_data = sanitize_data_for_ai(data)
            
            # Prepare prompt
            prompt = self._prepare_insights_prompt(sanitized_data, context)
            
            # Generate response
            response = model.generate_content(prompt)
            
            # Format response
            formatted = format_ai_response(response)
            
            if formatted['success']:
                return {
                    'insights': formatted['text'],
                    'confidence': 0.85,  # Placeholder confidence score
                    'generated_at': 'now',
                    'success': True
                }
            else:
                return {
                    'insights': '',
                    'error': formatted['error'],
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
            return {
                'insights': '',
                'error': str(e),
                'success': False
            }
    
    @measure_performance
    @retry_on_failure(max_retries=2, delay=1)
    def forecast_metrics(self, historical_data, periods=30, metric_name="metric"):
        """
        Generate forecasts based on historical data.
        
        Args:
            historical_data: List of historical values
            periods: Number of periods to forecast
            metric_name: Name of the metric being forecasted
            
        Returns:
            dict: Forecast data with predictions and confidence intervals
        """
        try:
            model = self._get_model()
            
            # Prepare forecast prompt
            prompt = self._prepare_forecast_prompt(historical_data, periods, metric_name)
            
            # Generate response
            response = model.generate_content(prompt)
            
            # Parse forecast from response
            formatted = format_ai_response(response)
            
            if formatted['success']:
                # Extract forecast values (simplified - would need proper parsing)
                return {
                    'predictions': [],  # Would parse from AI response
                    'confidence_intervals': [],
                    'trend': 'stable',
                    'success': True
                }
            else:
                return {
                    'predictions': [],
                    'error': formatted['error'],
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Failed to generate forecast: {str(e)}")
            return {
                'predictions': [],
                'error': str(e),
                'success': False
            }
    
    @measure_performance
    def analyze_trends(self, data):
        """
        Analyze trends and patterns in data.
        
        Args:
            data: Data to analyze
            
        Returns:
            dict: Trend analysis results
        """
        try:
            model = self._get_model()
            
            # Sanitize data
            sanitized_data = sanitize_data_for_ai(data)
            
            # Prepare prompt
            prompt = self._prepare_trend_analysis_prompt(sanitized_data)
            
            # Generate response
            response = model.generate_content(prompt)
            
            formatted = format_ai_response(response)
            
            if formatted['success']:
                return {
                    'trends': formatted['text'],
                    'patterns': [],
                    'success': True
                }
            else:
                return {
                    'trends': '',
                    'error': formatted['error'],
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze trends: {str(e)}")
            return {
                'trends': '',
                'error': str(e),
                'success': False
            }
    
    @measure_performance
    def generate_recommendations(self, analysis):
        """
        Generate actionable recommendations based on analysis.
        
        Args:
            analysis: Analysis data
            
        Returns:
            list: List of recommendation dictionaries
        """
        try:
            model = self._get_model()
            
            # Prepare prompt
            prompt = self._prepare_recommendations_prompt(analysis)
            
            # Generate response
            response = model.generate_content(prompt)
            
            formatted = format_ai_response(response)
            
            if formatted['success']:
                # Parse recommendations from response
                return {
                    'recommendations': [
                        {
                            'title': 'Sample Recommendation',
                            'description': formatted['text'],
                            'priority': 'medium',
                            'expected_impact': 'high'
                        }
                    ],
                    'success': True
                }
            else:
                return {
                    'recommendations': [],
                    'error': formatted['error'],
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return {
                'recommendations': [],
                'error': str(e),
                'success': False
            }
    
    def _prepare_insights_prompt(self, data, context):
        """Prepare prompt for insights generation."""
        return f"""
        Analyze the following educational data and provide actionable insights:
        
        Context: {context}
        
        Data: {json.dumps(data, indent=2)}
        
        Please provide:
        1. Key observations
        2. Patterns or trends
        3. Areas of concern
        4. Positive highlights
        5. Actionable recommendations
        
        Keep the response concise and focused on actionable insights.
        """
    
    def _prepare_forecast_prompt(self, historical_data, periods, metric_name):
        """Prepare prompt for forecasting."""
        return f"""
        Based on the following historical data for {metric_name}, forecast the next {periods} periods:
        
        Historical Data: {json.dumps(historical_data)}
        
        Please provide:
        1. Predicted values for the next {periods} periods
        2. Confidence level for the forecast
        3. Trend direction (increasing, decreasing, stable)
        4. Key factors influencing the forecast
        
        Format the response as a structured prediction.
        """
    
    def _prepare_trend_analysis_prompt(self, data):
        """Prepare prompt for trend analysis."""
        return f"""
        Analyze the following data for trends and patterns:
        
        Data: {json.dumps(data, indent=2)}
        
        Please identify:
        1. Overall trends (increasing, decreasing, cyclical, stable)
        2. Significant patterns or anomalies
        3. Correlations between different metrics
        4. Seasonal or periodic variations
        
        Provide a clear, concise analysis.
        """
    
    def _prepare_recommendations_prompt(self, analysis):
        """Prepare prompt for recommendations."""
        return f"""
        Based on the following analysis, provide actionable recommendations:
        
        Analysis: {json.dumps(analysis, indent=2)}
        
        For each recommendation, provide:
        1. Clear title
        2. Detailed description
        3. Priority level (high, medium, low)
        4. Expected impact
        5. Implementation steps
        
        Focus on practical, implementable recommendations.
        """


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

_gemini_client_instance = None


def get_gemini_client():
    """
    Get singleton Gemini client instance.
    
    Returns:
        GeminiClient: Configured Gemini client
    """
    global _gemini_client_instance
    
    if _gemini_client_instance is None:
        try:
            _gemini_client_instance = GeminiClient()
        except ValueError as e:
            logger.warning(f"Gemini client not available: {str(e)}")
            return None
    
    return _gemini_client_instance


def prepare_prompt(template, data):
    """
    Prepare prompt for Gemini from template and data.
    
    Args:
        template: Prompt template string
        data: Data to inject into template
        
    Returns:
        str: Formatted prompt
    """
    try:
        return template.format(**data)
    except KeyError as e:
        logger.error(f"Missing key in prompt template: {str(e)}")
        return template


def parse_ai_response(response):
    """
    Parse and structure AI response.
    
    Args:
        response: Raw AI response
        
    Returns:
        dict: Structured response data
    """
    formatted = format_ai_response(response)
    
    if formatted['success']:
        # Try to parse as JSON if possible
        try:
            parsed = json.loads(formatted['text'])
            return parsed
        except json.JSONDecodeError:
            # Return as plain text if not JSON
            return {'text': formatted['text']}
    else:
        return {'error': formatted['error']}


def cache_ai_result(key, result, ttl=3600):
    """
    Cache AI result in Redis.
    
    Args:
        key: Cache key
        result: Result to cache
        ttl: Time to live in seconds
    """
    cache_key = f"ai_result:{key}"
    cache.set(cache_key, result, ttl)
    logger.debug(f"Cached AI result: {cache_key}")


def get_cached_ai_result(key):
    """
    Retrieve cached AI result.
    
    Args:
        key: Cache key
        
    Returns:
        Cached result or None
    """
    cache_key = f"ai_result:{key}"
    result = cache.get(cache_key)
    
    if result:
        logger.debug(f"Cache hit for AI result: {cache_key}")
    
    return result
