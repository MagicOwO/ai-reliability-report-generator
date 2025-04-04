from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any
import re
from urllib.parse import urljoin
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class StatusPageScraper(BaseScraper):
    """Scraper for New Relic Status Page"""

    def __init__(self, base_url: str, company_name: str):
        super().__init__(base_url)
        self.company_name = company_name

    async def fetch_incidents(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch incidents between start_date and end_date
        
        Args:
            start_date: Start date for incident fetching
            end_date: End date for incident fetching
            
        Returns:
            List of incidents with their details
        """
        logger.info(f"Fetching incidents from {start_date} to {end_date}")
        content = await self._fetch_page(self.base_url)
        return await self.parse_page(content)

    async def parse_page(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse page content to extract incidents
        
        Args:
            content: HTML content of the page
            
        Returns:
            List of incidents with their details
        """
        soup = BeautifulSoup(content, 'html.parser')
        logger.debug(f"Page title: {soup.title.string if soup.title else 'No title found'}")

        incidents = []
        incident_elements = soup.find_all(class_='incident-container')
        logger.debug(f"Found {len(incident_elements)} potential incidents")
        
        if incident_elements:
            sample = incident_elements[0]
            logger.debug(f"Sample incident HTML: {sample}")

        for incident in incident_elements:
            try:
                parsed_incident = self._parse_incident(incident)
                if parsed_incident:
                    # Convert date string to datetime object
                    if parsed_incident['date']:
                        parsed_incident['date'] = self._parse_date(parsed_incident['date'])
                    else:
                        parsed_incident['date'] = datetime.now()
                        
                    # Add company name to incident
                    parsed_incident['company'] = self.company_name
                    
                    # Extract duration
                    parsed_incident['duration'] = self._extract_duration(parsed_incident['description'])
                    
                    # Add category placeholder (will be determined by analyzer)
                    parsed_incident['category'] = 'Uncategorized'
                    
                    incidents.append(parsed_incident)
            except Exception as e:
                logger.error(f"Error parsing incident: {str(e)}")
                continue

        logger.info(f"Successfully parsed {len(incidents)} incidents")
        return incidents

    def _parse_incident(self, incident_element) -> Dict[str, Any]:
        """
        Parse an individual incident element
        
        Args:
            incident_element: BeautifulSoup element containing incident information
            
        Returns:
            Dictionary containing incident details
        """
        try:
            # Extract title
            title_element = incident_element.find(class_='incident-title')
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            # Extract date
            date_element = incident_element.find(class_='incident-time')
            date_str = date_element.get_text(strip=True) if date_element else None
            
            # Extract status
            status_element = incident_element.find(class_='incident-status')
            status = status_element.get_text(strip=True) if status_element else "Unknown"
            
            # Extract description
            desc_element = incident_element.find(class_='incident-description')
            description = desc_element.get_text(strip=True) if desc_element else ""
            
            logger.debug(f"Parsed incident: {title} ({date_str})")
            
            return {
                'title': title,
                'date': date_str,
                'status': status,
                'description': description
            }
        except Exception as e:
            logger.error(f"Error parsing incident element: {str(e)}")
            return None

    def _get_page_url(self, page_num: int) -> str:
        """Generate URL for the specified page number"""
        if page_num == 1:
            return self.base_url
        return f"{self.base_url}?page={page_num}"

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string into datetime object
        
        Args:
            date_str: Date string to parse
            
        Returns:
            datetime object
        """
        if not date_str:
            logger.warning("Empty date string")
            return datetime.now()

        try:
            # New Relic uses ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError as e:
            logger.warning(f"Could not parse date string: {date_str} - {str(e)}")
            return datetime.now()

    def _extract_duration(self, description: str) -> str:
        """
        Extract incident duration from description
        
        Args:
            description: Incident description text
            
        Returns:
            Duration string if found, else 'Unknown'
        """
        duration_patterns = [
            r'lasted (\d+\s+(?:minute|hour|day)s?)',
            r'duration[:\s]+(\d+\s+(?:minute|hour|day)s?)',
            r'(\d+\s+(?:minute|hour|day)s?)\s+of\s+(?:downtime|disruption)',
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, description, re.I)
            if match:
                return match.group(1)

        return "Unknown" 