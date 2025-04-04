import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import logging
import yaml
import json
import argparse
import pandas as pd

from .scrapers.status_page_scraper import StatusPageScraper
from .analyzers.incident_analyzer import IncidentAnalyzer
from .analyzers.ai_analyzer import AIIncidentAnalyzer, DEFAULT_OPENAI_API_KEY
from .utils.excel_generator import ExcelReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReliabilityReportGenerator:
    """Main class for generating reliability reports"""

    def __init__(self, config: Dict[str, Any], api_key: str = None):
        """
        Initialize the report generator
        
        Args:
            config: Configuration dictionary containing:
                - target_company: Dict with name and status_url
                - peer_companies: List of dicts with name and status_url
                - timeframe: Dict with start_date and end_date
            api_key: OpenAI API key for AI analysis
        """
        self.config = config
        self.target_company = config['target_company']
        self.peer_companies = config['peer_companies']
        self.start_date = datetime.strptime(config['timeframe']['start_date'], '%Y-%m-%d')
        self.end_date = datetime.strptime(config['timeframe']['end_date'], '%Y-%m-%d')
        self.api_key = api_key
        self.ai_enabled = True  # Always enabled, will use default key if none provided
        logger.info(f"Initialized generator for {self.target_company['name']} with AI analysis")

    async def generate_report(self):
        """Generate the comprehensive reliability report including AI analysis"""
        logger.info("Starting comprehensive report generation...")
        
        # Create output directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)
        logger.info("Created reports directory")
        
        # Fetch incidents for all companies
        logger.info("Fetching incidents...")
        all_incidents = await self._fetch_all_incidents()
        logger.info(f"Found {len(all_incidents)} total incidents")
        
        # Separate target and peer incidents
        target_incidents = [
            incident for incident in all_incidents 
            if incident['company'] == self.target_company['name']
        ]
        peer_incidents = [
            incident for incident in all_incidents 
            if incident['company'] != self.target_company['name']
        ]
        logger.info(f"Target company incidents: {len(target_incidents)}")
        logger.info(f"Peer companies incidents: {len(peer_incidents)}")
        
        # Analyze incidents with standard analyzer
        logger.info("Analyzing incidents with standard analyzer...")
        standard_analyzer = IncidentAnalyzer()
        target_standard_analysis = standard_analyzer.analyze_incidents(target_incidents)
        peer_standard_analysis = standard_analyzer.analyze_incidents(peer_incidents)
        logger.info("Standard analysis complete")
        
        # AI analysis is always performed
        ai_analysis = None
        try:
            logger.info("Starting AI-powered analysis...")
            ai_analyzer = AIIncidentAnalyzer(api_key=self.api_key)
            ai_analysis = ai_analyzer.analyze_incidents(target_incidents, peer_incidents)
            logger.info("AI analysis complete")
            
            # Process and enhance incidents with AI analysis
            self._process_ai_analysis_results(target_incidents, peer_incidents, ai_analysis)
            
            # Save AI analysis to JSON file for reference
            analysis_path = f"reports/{self.target_company['name']}_ai_analysis.json"
            with open(analysis_path, 'w') as f:
                json.dump(ai_analysis, f, indent=2, default=str)
            logger.info(f"AI analysis saved to {analysis_path}")
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}", exc_info=True)
            logger.warning("Continuing without AI analysis")
        
        # Generate comprehensive report
        report_filename = f"{self.target_company['name']}_reliability_report"
        
        # 1. Generate Excel report
        excel_path = f"reports/{report_filename}.xlsx"
        logger.info(f"Generating Excel report: {excel_path}")
        excel_generator = ExcelReportGenerator(excel_path)
        excel_generator.generate_report(target_incidents, target_standard_analysis, ai_analysis)
        logger.info("Excel report generated successfully")
        
        # 2. Generate detailed text report
        text_report_path = self._generate_text_report(
            report_filename, 
            target_incidents, 
            peer_incidents,
            target_standard_analysis, 
            peer_standard_analysis,
            ai_analysis
        )
        
        # Return analysis results
        return {
            'target_analysis': target_standard_analysis,
            'peer_analysis': peer_standard_analysis,
            'ai_analysis': ai_analysis,
            'excel_report_path': excel_path,
            'text_report_path': text_report_path
        }

    def _process_ai_analysis_results(self, target_incidents, peer_incidents, ai_analysis):
        """
        Process AI analysis results and enhance incident data with summaries and categorization
        
        Args:
            target_incidents: List of target company incidents
            peer_incidents: List of peer company incidents
            ai_analysis: Results from AI analysis
        """
        if not ai_analysis:
            logger.warning("No AI analysis available to process")
            return
            
        logger.info("Processing AI analysis results and enhancing incident data...")
        
        # Get categorized incidents from AI analysis
        target_categorized = ai_analysis.get('target_analysis', {}).get('categorized_incidents', [])
        peer_categorized = ai_analysis.get('peer_analysis', {}).get('categorized_incidents', [])
        
        # Create a map of categories
        categories = {}
        for cat in ai_analysis.get('target_analysis', {}).get('categories', []):
            categories[cat.get('name')] = cat.get('description', '')
            
        # Add peer categories if they exist
        for cat in ai_analysis.get('peer_analysis', {}).get('categories', []):
            if cat.get('name') not in categories:
                categories[cat.get('name')] = cat.get('description', '')
        
        # Update target incidents with AI-enhanced information
        for i, incident in enumerate(target_incidents):
            # Find corresponding categorized incident
            for cat_incident in target_categorized:
                if cat_incident.get('incident_id') == i:
                    incident['ai_category'] = cat_incident.get('category', 'Uncategorized')
                    incident['severity'] = cat_incident.get('severity', 'Unknown')
                    incident['root_cause'] = cat_incident.get('root_cause', 'Unknown')
                    
                    # Add category description
                    if incident['ai_category'] in categories:
                        incident['category_description'] = categories[incident['ai_category']]
                    
                    # Update duration if it was unknown
                    if incident.get('duration') == 'Unknown' and 'duration_hours' in cat_incident:
                        duration_hours = cat_incident['duration_hours']
                        if duration_hours < 1:
                            incident['duration'] = f"{int(duration_hours * 60)} minutes"
                        else:
                            incident['duration'] = f"{duration_hours} hours"
                    break
        
        # Similarly update peer incidents
        for i, incident in enumerate(peer_incidents):
            for cat_incident in peer_categorized:
                if cat_incident.get('incident_id') == i:
                    incident['ai_category'] = cat_incident.get('category', 'Uncategorized')
                    incident['severity'] = cat_incident.get('severity', 'Unknown')
                    incident['root_cause'] = cat_incident.get('root_cause', 'Unknown')
                    
                    if incident['ai_category'] in categories:
                        incident['category_description'] = categories[incident['ai_category']]
                    
                    if incident.get('duration') == 'Unknown' and 'duration_hours' in cat_incident:
                        duration_hours = cat_incident['duration_hours']
                        if duration_hours < 1:
                            incident['duration'] = f"{int(duration_hours * 60)} minutes"
                        else:
                            incident['duration'] = f"{duration_hours} hours"
                    break
        
        logger.info("Incident data enhanced with AI analysis")

    def _generate_text_report(self, report_filename, target_incidents, peer_incidents, 
                             target_analysis, peer_analysis, ai_analysis):
        """
        Generate a comprehensive text report with analysis results
        
        Args:
            report_filename: Base filename for the report
            target_incidents: List of target company incidents
            peer_incidents: List of peer company incidents
            target_analysis: Standard analysis of target incidents
            peer_analysis: Standard analysis of peer incidents
            ai_analysis: AI-powered analysis results
            
        Returns:
            Path to the generated text report
        """
        report_path = f"reports/{report_filename}.md"
        logger.info(f"Generating comprehensive text report: {report_path}")
        
        with open(report_path, 'w') as f:
            # Report Header
            f.write(f"# Reliability Report for {self.target_company['name']}\n\n")
            f.write(f"**Time Period:** {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}\n\n")
            f.write(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            if ai_analysis and 'target_analysis' in ai_analysis and 'summary' in ai_analysis['target_analysis']:
                f.write(f"{ai_analysis['target_analysis']['summary']}\n\n")
            else:
                f.write(f"During the analyzed period, {self.target_company['name']} experienced {len(target_incidents)} incidents ")
                f.write(f"across {len(target_analysis['categories'])} categories.\n\n")
            
            # Reliability Status and Trends
            f.write("## Reliability Status and Trends\n\n")
            
            if ai_analysis and 'target_analysis' in ai_analysis and 'trends' in ai_analysis['target_analysis']:
                trends = ai_analysis['target_analysis']['trends']
                f.write(f"**Overall Trend:** {trends.get('overall', 'Unknown')}\n\n")
                
                if 'by_category' in trends:
                    f.write("**Trends by Category:**\n\n")
                    for category, trend in trends['by_category'].items():
                        f.write(f"- {category}: {trend}\n")
                    f.write("\n")
            else:
                f.write("Based on standard analysis:\n\n")
                if 'trends' in target_analysis and 'trend' in target_analysis['trends']:
                    f.write(f"**Overall Trend:** {target_analysis['trends']['trend']}\n\n")
                
                if 'monthly_distribution' in target_analysis.get('trends', {}):
                    f.write("**Monthly Incident Distribution:**\n\n")
                    for month, count in target_analysis['trends']['monthly_distribution'].items():
                        f.write(f"- {month}: {count} incidents\n")
                    f.write("\n")
            
            # Key Reliability Issues
            f.write("## Key Reliability Issues\n\n")
            
            if ai_analysis and 'target_analysis' in ai_analysis and 'key_issues' in ai_analysis['target_analysis']:
                key_issues = ai_analysis['target_analysis']['key_issues']
                for i, issue in enumerate(key_issues):
                    f.write(f"### {i+1}. {issue.get('title', 'Unknown Issue')}\n\n")
                    f.write(f"**Impact:** {issue.get('impact', 'Unknown')}\n\n")
                    f.write(f"**Description:** {issue.get('description', 'No description available')}\n\n")
                    if 'frequency' in issue:
                        f.write(f"**Frequency:** {issue['frequency']}\n\n")
            else:
                key_issues = target_analysis.get('key_issues', [])
                for i, issue in enumerate(key_issues):
                    f.write(f"### {i+1}. {issue.get('title', 'Unknown Issue')}\n\n")
                    f.write(f"**Impact:** {issue.get('impact', 'Unknown')}\n\n")
                    f.write(f"**Frequency:** {issue.get('count', 0)} occurrences\n\n")
            
            # Incident Categories
            f.write("## Incident Categories\n\n")
            
            if ai_analysis and 'target_analysis' in ai_analysis and 'categories' in ai_analysis['target_analysis']:
                categories = ai_analysis['target_analysis']['categories']
                for cat in categories:
                    f.write(f"### {cat.get('name', 'Unknown Category')}\n\n")
                    f.write(f"**Description:** {cat.get('description', 'No description available')}\n\n")
                    if 'example_incident' in cat:
                        f.write(f"**Example:** {cat['example_incident']}\n\n")
            else:
                for category, data in target_analysis['categories'].items():
                    f.write(f"### {category}\n\n")
                    f.write(f"**Count:** {data['count']} incidents ({data.get('percentage', 0):.1f}%)\n\n")
                    if data['incidents']:
                        example = data['incidents'][0]
                        f.write(f"**Example:** {example.get('title', 'No title')}\n\n")
            
            # Comparative Analysis
            f.write("## Comparative Analysis with Peer Companies\n\n")
            
            if ai_analysis and 'comparative_analysis' in ai_analysis:
                comparative = ai_analysis['comparative_analysis']
                
                if 'trend_comparison' in comparative:
                    f.write(f"**Trend Comparison:** {comparative['trend_comparison']}\n\n")
                
                if 'common_categories' in comparative:
                    f.write("**Common Categories with Peers:**\n\n")
                    for cat in comparative['common_categories']:
                        f.write(f"- {cat}\n")
                    f.write("\n")
                
                if 'target_unique_categories' in comparative:
                    f.write("**Categories Unique to Target Company:**\n\n")
                    for cat in comparative['target_unique_categories']:
                        f.write(f"- {cat}\n")
                    f.write("\n")
                
                if 'peer_unique_categories' in comparative:
                    f.write("**Categories Unique to Peer Companies:**\n\n")
                    for cat in comparative['peer_unique_categories']:
                        f.write(f"- {cat}\n")
                    f.write("\n")
                
                if 'summary' in comparative:
                    f.write(f"**Summary:** {comparative['summary']}\n\n")
            else:
                f.write(f"{self.target_company['name']} had {len(target_incidents)} incidents compared to a total of {len(peer_incidents)} incidents across all peer companies.\n\n")
                
                # Calculate average incidents per peer
                avg_peer_incidents = len(peer_incidents) / len(self.peer_companies) if self.peer_companies else 0
                f.write(f"**Average incidents per peer company:** {avg_peer_incidents:.1f}\n\n")
            
            # Detailed Incident List
            f.write("## Detailed Incident List\n\n")
            f.write("See the accompanying Excel spreadsheet for a detailed list of all incidents.\n\n")
            f.write(f"**Spreadsheet Location:** {report_filename}.xlsx\n\n")
            
            # Methodology
            f.write("## Methodology\n\n")
            f.write("This report was generated using a combination of automated data collection and AI-powered analysis:\n\n")
            f.write("1. **Data Collection:** Incident data was collected from the public status pages of the target company and peer companies.\n")
            f.write("2. **Basic Analysis:** Statistical analysis was performed to identify trends and patterns in the incident data.\n")
            f.write("3. **AI Analysis:** OpenAI's GPT-4o model was used to provide deeper insights, categorization, and comparative analysis.\n")
            f.write("4. **Report Generation:** The final report combines standard metrics with AI-enhanced insights to provide a comprehensive view of reliability status.\n\n")
            
            # Conclusion
            f.write("## Conclusion\n\n")
            if ai_analysis and 'target_analysis' in ai_analysis and 'summary' in ai_analysis['target_analysis']:
                f.write(f"{ai_analysis['target_analysis']['summary']}\n\n")
                f.write("For more detailed information, please review the key issues and incident categories sections of this report.\n")
            else:
                f.write(f"This report provides an overview of {self.target_company['name']}'s reliability during the analyzed period. ")
                f.write("The data collected and analyzed can be used to identify areas for improvement and track reliability trends over time.\n")
        
        logger.info(f"Text report generated at {report_path}")
        return report_path

    async def _fetch_all_incidents(self) -> List[Dict[str, Any]]:
        """Fetch incidents from all companies"""
        all_incidents = []
        
        # Create tasks for all companies
        tasks = []
        companies = [self.target_company] + self.peer_companies
        
        for company in companies:
            logger.info(f"Creating task for {company['name']}")
            scraper = StatusPageScraper(company['status_url'], company['name'])
            tasks.append(self._fetch_company_incidents(scraper))
            
        # Run all tasks concurrently
        logger.info("Starting concurrent fetching...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for company_incidents in results:
            if isinstance(company_incidents, Exception):
                logger.error(f"Error fetching incidents: {str(company_incidents)}")
                continue
            all_incidents.extend(company_incidents)
            
        return all_incidents

    async def _fetch_company_incidents(self, scraper: StatusPageScraper) -> List[Dict[str, Any]]:
        """Fetch incidents for a single company"""
        async with scraper:
            try:
                logger.info(f"Fetching incidents for {scraper.company_name}")
                incidents = await scraper.fetch_incidents(self.start_date, self.end_date)
                logger.info(f"Found {len(incidents)} incidents for {scraper.company_name}")
                
                # Add company name to each incident
                for incident in incidents:
                    incident['company'] = scraper.company_name
                
                return incidents
            except Exception as e:
                logger.error(f"Error fetching incidents for {scraper.company_name}: {str(e)}")
                return []

async def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Generate reliability reports')
        parser.add_argument('--config', type=str, default='config/default_config.yaml',
                            help='Path to configuration file')
        parser.add_argument('--api-key', type=str,
                            help='OpenAI API key for AI analysis')
        args = parser.parse_args()
        
        logger.info("Starting report generator")
        
        # Load configuration from YAML
        try:
            logger.info(f"Loading configuration from {args.config}")
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded for target company: {config['target_company']['name']}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
        
        # Check if API key is provided
        api_key = args.api_key
        if not api_key:
            # Try to get API key from environment variable
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                logger.info("Using OpenAI API key from environment variable")
            else:
                logger.warning("No OpenAI API key provided. Using default key.")
                logger.warning("Make sure to replace the placeholder in src/analyzers/ai_analyzer.py with a valid key.")
        
        # Create and run the report generator
        generator = ReliabilityReportGenerator(config, api_key=api_key)
        result = await generator.generate_report()
        
        logger.info(f"Excel report generated successfully at: {result['excel_report_path']}")
        logger.info(f"Text report generated successfully at: {result['text_report_path']}")
        logger.info(f"Target company '{config['target_company']['name']}' had {result['target_analysis']['total_incidents']} incidents")
        
        if result['target_analysis']['total_incidents'] > 0:
            logger.info(f"Main categories: {', '.join(result['target_analysis']['categories'].keys())}")
            
        # Print AI analysis summary if available
        if result.get('ai_analysis'):
            target_analysis = result['ai_analysis'].get('target_analysis', {})
            if 'summary' in target_analysis:
                logger.info("AI Analysis Summary:")
                logger.info(target_analysis['summary'])
                
    except Exception as e:
        logger.error(f"Error running report generator: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting async event loop")
        asyncio.run(main())
        logger.info("Report generator completed successfully")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program execution failed: {str(e)}", exc_info=True) 