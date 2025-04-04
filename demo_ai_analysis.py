#!/usr/bin/env python3
"""
Demo script showing how to use the integrated AI analyzer with sample data.
This script demonstrates the functionality without needing to scrape websites.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
import argparse
import logging
from src.analyzers.ai_analyzer import AIIncidentAnalyzer, DEFAULT_OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample incidents data
TARGET_INCIDENTS = [
    {
        "company": "New Relic",
        "date": datetime.now() - timedelta(days=5),
        "title": "Infrastructure Alerts- False Host Not Reporting",
        "description": "The restoration of affected entity metadata has been completed. Impacted services have returned to normal operations.",
        "status": "Resolved",
        "duration": "2 days, 4 hours",
        "category": "Infrastructure"
    },
    {
        "company": "New Relic",
        "date": datetime.now() - timedelta(days=15),
        "title": "Data Irregularities in the EU Region",
        "description": "Some customers experienced data irregularities in the EU region. The issue has been resolved.",
        "status": "Resolved",
        "duration": "3 hours",
        "category": "Data Processing"
    },
    {
        "company": "New Relic",
        "date": datetime.now() - timedelta(days=30),
        "title": "Scheduled Maintenance for the US & EU Regions",
        "description": "Scheduled maintenance for the US & EU Regions has been completed successfully.",
        "status": "Completed",
        "duration": "1.5 hours",
        "category": "Maintenance"
    }
]

PEER_INCIDENTS = [
    {
        "company": "MongoDB",
        "date": datetime.now() - timedelta(days=3),
        "title": "Intermittent connection issues for some clusters in the AWS Frankfurt region",
        "description": "We have received confirmation that this issue has been resolved by taking a host offline in the AWS network that was causing the DNS resolution issues.",
        "status": "Resolved",
        "duration": "23 hours",
        "category": "Uncategorized"
    },
    {
        "company": "Snowflake",
        "date": datetime.now() - timedelta(days=10),
        "title": "AWS - Europe (Stockholm): INC0126513 (Degraded Performance)",
        "description": "Some users experienced degraded performance in the Stockholm region. The issue has been resolved.",
        "status": "Resolved",
        "duration": "45 minutes",
        "category": "Uncategorized"
    },
    {
        "company": "SignalFx",
        "date": datetime.now() - timedelta(days=20),
        "title": "Splunk APM Trace Data Ingestion Delayed",
        "description": "This incident has been resolved.",
        "status": "Resolved",
        "duration": "2.5 hours",
        "category": "Uncategorized"
    },
    {
        "company": "Confluent",
        "date": datetime.now() - timedelta(days=25),
        "title": "Errors connecting to Kafka in Azure/canadacentral",
        "description": "From approximately 02:23 - 02:43 UTC, customers connecting to Kafka clusters in Azure/canadacentral may have experienced errors.",
        "status": "Resolved",
        "duration": "20 minutes",
        "category": "Uncategorized"
    },
    {
        "company": "DigitalOcean",
        "date": datetime.now() - timedelta(days=7),
        "title": "Cloud Control Panel and API",
        "description": "Engineers have implemented a fix and are monitoring the system. The Cloud Control Panel and API are now functioning normally.",
        "status": "Resolved",
        "duration": "1.5 hours",
        "category": "Uncategorized"
    }
]

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Demo AI analysis with sample data')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    args = parser.parse_args()
    
    # Check for API key
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    
    # If no API key is provided, will use the default one
    if not api_key:
        logger.warning("No API key provided via --api-key or OPENAI_API_KEY environment variable.")
        logger.warning(f"Using default API key. Make sure to replace the placeholder in src/analyzers/ai_analyzer.py with a valid key.")
    
    try:
        # Create output directory
        os.makedirs('reports', exist_ok=True)
        
        # Initialize AI analyzer with API key
        logger.info("Initializing AI analyzer...")
        ai_analyzer = AIIncidentAnalyzer(api_key=api_key)
        
        # Run analysis on sample data
        logger.info("Running AI analysis on sample incidents...")
        analysis_result = ai_analyzer.analyze_incidents(TARGET_INCIDENTS, PEER_INCIDENTS)
        
        # Save analysis to JSON file
        output_path = 'reports/demo_ai_analysis.json'
        with open(output_path, 'w') as f:
            json.dump(analysis_result, f, indent=2, default=str)
        
        logger.info(f"Analysis saved to {output_path}")
        
        # Display a summary of the analysis
        target_analysis = analysis_result.get('target_analysis', {})
        if 'summary' in target_analysis:
            logger.info("\nAI Analysis Summary:")
            logger.info(target_analysis['summary'])
        
        # Display categories
        if 'categories' in target_analysis:
            logger.info("\nIncident Categories:")
            for idx, category in enumerate(target_analysis['categories']):
                logger.info(f"{idx+1}. {category.get('name')}: {category.get('description')}")
        
        # Display key issues
        if 'key_issues' in target_analysis:
            logger.info("\nKey Issues:")
            for idx, issue in enumerate(target_analysis['key_issues']):
                logger.info(f"{idx+1}. {issue.get('title')} (Impact: {issue.get('impact', 'Unknown')})")
        
        # Display comparative analysis
        comparative = analysis_result.get('comparative_analysis', {})
        if 'trend_comparison' in comparative:
            logger.info("\nComparative Analysis:")
            logger.info(comparative['trend_comparison'])
        
    except Exception as e:
        logger.error(f"Error running AI analysis: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 