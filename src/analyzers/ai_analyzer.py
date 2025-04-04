import logging
import json
from typing import List, Dict, Any
import openai
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Default API key - Replace with your actual API key
DEFAULT_OPENAI_API_KEY = "your-openai-api-key-here"

class AIIncidentAnalyzer:
    """
    Analyzer that uses AI to categorize incidents and extract key insights
    """
    
    def __init__(self, api_key=None):
        """Initialize the AI analyzer with API key"""
        # Try to get API key from parameters, environment variable, or use default
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or DEFAULT_OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def analyze_incidents(self, 
                         target_incidents: List[Dict[str, Any]], 
                         peer_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use AI to analyze incidents and provide deeper insights
        
        Args:
            target_incidents: List of incidents from the target company
            peer_incidents: List of incidents from peer companies
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting AI analysis for {len(target_incidents)} target incidents and {len(peer_incidents)} peer incidents")
        
        # Extract insights from peer incidents first to establish categories
        peer_analysis = self._analyze_with_ai(peer_incidents, "peer")
        
        # Analyze target incidents using the same categories
        if peer_analysis and "categories" in peer_analysis:
            target_analysis = self._analyze_with_ai(target_incidents, "target", peer_analysis["categories"])
        else:
            target_analysis = self._analyze_with_ai(target_incidents, "target")
        
        # Combine the analyses
        combined_analysis = {
            "target_analysis": target_analysis,
            "peer_analysis": peer_analysis,
            "comparative_analysis": self._generate_comparative_analysis(target_analysis, peer_analysis)
        }
        
        logger.info("AI analysis completed successfully")
        return combined_analysis
    
    def _analyze_with_ai(self, incidents: List[Dict[str, Any]], 
                        company_type: str, 
                        existing_categories: List[Dict] = None) -> Dict[str, Any]:
        """
        Send incidents to the AI model for analysis
        
        Args:
            incidents: List of incidents to analyze
            company_type: 'target' or 'peer'
            existing_categories: Optional list of categories from peer analysis
            
        Returns:
            Dictionary containing analysis results
        """
        if not incidents:
            logger.warning(f"No {company_type} incidents to analyze")
            return {
                "categories": [],
                "key_issues": [],
                "trends": {"overall": "No data available"},
                "summary": f"No incidents found for {company_type} companies."
            }
        
        # Prepare incidents for AI processing
        processed_incidents = []
        for incident in incidents:
            # Convert datetime objects to strings
            incident_copy = incident.copy()
            if isinstance(incident_copy.get('date'), datetime):
                incident_copy['date'] = incident_copy['date'].isoformat()
            processed_incidents.append(incident_copy)
            
        # Prepare prompt with existing categories if available
        categories_context = ""
        if existing_categories:
            categories_json = json.dumps(existing_categories, indent=2)
            categories_context = f"Use these existing categories from peer analysis: {categories_json}"
            
        # Define the system prompt
        system_prompt = f"""
        You are an expert reliability analyst. Your task is to analyze a set of incidents from {'the target company' if company_type == 'target' else 'peer companies'} and provide structured insights.
        
        {categories_context}
        
        Analyze the incidents to:
        1. Categorize each incident (create meaningful categories based on the type of issue)
        2. Identify key reliability issues and patterns
        3. Detect trends in incident frequency and severity
        4. Provide a summary of the reliability status
        
        Format your response as a JSON object with the following structure:
        {{
            "categories": [
                {{
                    "name": "Category name",
                    "description": "Detailed description of this category",
                    "example_incident": "Example of an incident in this category"
                }}
            ],
            "categorized_incidents": [
                {{
                    "incident_id": 0,  // Index in the original incidents array
                    "category": "Assigned category",
                    "severity": "Critical|Major|Minor|Low",
                    "duration_hours": 2.5,  // Estimated duration in hours if unknown
                    "root_cause": "Identified root cause if possible"
                }}
            ],
            "key_issues": [
                {{
                    "title": "Issue title",
                    "description": "Description of the issue",
                    "impact": "High|Medium|Low",
                    "frequency": "Number of occurrences"
                }}
            ],
            "trends": {{
                "overall": "increasing|decreasing|stable",
                "by_category": {{
                    "Category1": "increasing|decreasing|stable",
                    "Category2": "increasing|decreasing|stable"
                }}
            }},
            "summary": "Overall analysis summary in a paragraph"
        }}
        
        Ensure all incidents are categorized, even if you need to create a new category.
        """
        
        # Define the user message with the incidents
        user_message = f"Here are the incidents to analyze: {json.dumps(processed_incidents, indent=2)}"
        
        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for advanced analysis
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            analysis_result = json.loads(response.choices[0].message.content)
            logger.info(f"Successfully analyzed {len(incidents)} {company_type} incidents")
            
            # Update the incidents with categories, severity, and estimated duration
            self._update_incidents_with_ai_analysis(incidents, analysis_result.get("categorized_incidents", []))
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            # Return a basic structure in case of error
            return {
                "categories": [],
                "key_issues": [],
                "trends": {"overall": "Error in analysis"},
                "summary": f"Error analyzing {company_type} incidents: {str(e)}"
            }
    
    def _update_incidents_with_ai_analysis(self, 
                                         incidents: List[Dict[str, Any]], 
                                         categorized_incidents: List[Dict[str, Any]]):
        """
        Update the original incidents with AI-generated categories and insights
        
        Args:
            incidents: Original incidents list to update
            categorized_incidents: AI categorization results
        """
        for cat_incident in categorized_incidents:
            try:
                incident_id = cat_incident.get("incident_id", -1)
                if 0 <= incident_id < len(incidents):
                    # Update the incident with AI-provided information
                    incidents[incident_id]["category"] = cat_incident.get("category", "Uncategorized")
                    incidents[incident_id]["severity"] = cat_incident.get("severity", "Unknown")
                    
                    # Update duration if it was "Unknown"
                    if incidents[incident_id].get("duration") == "Unknown" and "duration_hours" in cat_incident:
                        hours = cat_incident["duration_hours"]
                        if hours < 1:
                            incidents[incident_id]["duration"] = f"{int(hours * 60)} minutes"
                        else:
                            incidents[incident_id]["duration"] = f"{hours} hours"
                    
                    # Add root cause if available
                    if "root_cause" in cat_incident:
                        incidents[incident_id]["root_cause"] = cat_incident["root_cause"]
            except Exception as e:
                logger.error(f"Error updating incident {incident_id}: {str(e)}")
    
    def _generate_comparative_analysis(self, 
                                     target_analysis: Dict[str, Any], 
                                     peer_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comparative analysis between target and peer companies
        
        Args:
            target_analysis: Analysis of target company incidents
            peer_analysis: Analysis of peer company incidents
            
        Returns:
            Dictionary containing comparative analysis
        """
        # Extract categories from both analyses
        target_categories = {cat["name"]: cat for cat in target_analysis.get("categories", [])}
        peer_categories = {cat["name"]: cat for cat in peer_analysis.get("categories", [])}
        
        # Find common and unique categories
        common_categories = set(target_categories.keys()) & set(peer_categories.keys())
        target_unique = set(target_categories.keys()) - set(peer_categories.keys())
        peer_unique = set(peer_categories.keys()) - set(target_categories.keys())
        
        # Prepare the comparative analysis
        comparative = {
            "common_categories": list(common_categories),
            "target_unique_categories": list(target_unique),
            "peer_unique_categories": list(peer_unique),
            "summary": "Comparative analysis between target and peer companies"
        }
        
        # Compare trends
        target_trend = target_analysis.get("trends", {}).get("overall", "Unknown")
        peer_trend = peer_analysis.get("trends", {}).get("overall", "Unknown")
        
        if target_trend != "Unknown" and peer_trend != "Unknown":
            if target_trend == peer_trend:
                comparative["trend_comparison"] = f"Both target and peer companies show {target_trend} incident trends."
            else:
                comparative["trend_comparison"] = f"Target company shows {target_trend} incident trends, while peer companies show {peer_trend} trends."
        
        return comparative 