from typing import List, Dict, Any
import re
from collections import defaultdict
from datetime import datetime, timedelta

class IncidentAnalyzer:
    """Analyzes and categorizes incidents"""

    # Predefined categories with their keywords
    CATEGORIES = {
        'API': ['api', 'endpoint', 'request', 'response', 'latency'],
        'Database': ['database', 'db', 'mysql', 'postgres', 'mongodb', 'redis', 'cache'],
        'Network': ['network', 'connectivity', 'dns', 'routing', 'traffic'],
        'Infrastructure': ['server', 'hardware', 'datacenter', 'infrastructure', 'capacity'],
        'Security': ['security', 'authentication', 'authorization', 'ssl', 'certificate'],
        'Performance': ['performance', 'slow', 'latency', 'timeout', 'degraded'],
        'Storage': ['storage', 'disk', 's3', 'blob', 'volume'],
        'UI/Frontend': ['ui', 'frontend', 'web', 'interface', 'dashboard'],
        'Scheduled Maintenance': ['maintenance', 'upgrade', 'scheduled', 'planned'],
        'Third-party': ['third-party', 'vendor', 'dependency', 'external'],
    }

    def __init__(self):
        self.incident_data = []

    def analyze_incidents(self, incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze incidents and generate report data
        
        Args:
            incidents: List of incident dictionaries
            
        Returns:
            Dictionary containing analysis results
        """
        self.incident_data = incidents
        
        return {
            'total_incidents': len(incidents),
            'categories': self._analyze_categories(),
            'trends': self._analyze_trends(),
            'severity_distribution': self._analyze_severity(),
            'mttr': self._calculate_mttr(),
            'key_issues': self._identify_key_issues()
        }

    def _categorize_incident(self, incident: Dict[str, Any]) -> str:
        """
        Categorize an incident based on its title and description
        
        Args:
            incident: Incident dictionary
            
        Returns:
            Category name
        """
        text = f"{incident['title']} {incident['description']}".lower()
        
        # Check each category's keywords
        for category, keywords in self.CATEGORIES.items():
            if any(keyword in text for keyword in keywords):
                return category
                
        return 'Other'

    def _analyze_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze incident distribution across categories
        
        Returns:
            Dictionary with category statistics
        """
        category_stats = defaultdict(lambda: {'count': 0, 'incidents': []})
        
        for incident in self.incident_data:
            category = self._categorize_incident(incident)
            category_stats[category]['count'] += 1
            category_stats[category]['incidents'].append(incident)
            
        # Calculate percentages
        total = len(self.incident_data)
        for stats in category_stats.values():
            stats['percentage'] = (stats['count'] / total * 100) if total > 0 else 0
            
        return dict(category_stats)

    def _analyze_trends(self) -> Dict[str, Any]:
        """
        Analyze incident trends over time
        
        Returns:
            Dictionary with trend analysis
        """
        if not self.incident_data:
            return {'trend': 'No data available'}
            
        # Sort incidents by date
        sorted_incidents = sorted(self.incident_data, key=lambda x: x['date'])
        
        # Group by month
        monthly_counts = defaultdict(int)
        for incident in sorted_incidents:
            month_key = incident['date'].strftime('%Y-%m')
            monthly_counts[month_key] += 1
            
        # Calculate trend
        counts = list(monthly_counts.values())
        if len(counts) > 1:
            trend = 'increasing' if counts[-1] > counts[0] else 'decreasing'
        else:
            trend = 'stable'
            
        return {
            'trend': trend,
            'monthly_distribution': dict(monthly_counts)
        }

    def _analyze_severity(self) -> Dict[str, int]:
        """
        Analyze incident severity distribution
        
        Returns:
            Dictionary with severity counts
        """
        severity_counts = defaultdict(int)
        
        for incident in self.incident_data:
            severity = self._determine_severity(incident)
            severity_counts[severity] += 1
            
        return dict(severity_counts)

    def _determine_severity(self, incident: Dict[str, Any]) -> str:
        """
        Determine incident severity based on keywords and duration
        
        Args:
            incident: Incident dictionary
            
        Returns:
            Severity level
        """
        text = f"{incident['title']} {incident['description']} {incident['status']}".lower()
        
        if any(word in text for word in ['critical', 'severe', 'outage', 'down']):
            return 'Critical'
        elif any(word in text for word in ['major', 'degraded', 'significant']):
            return 'Major'
        elif any(word in text for word in ['minor', 'partial', 'limited']):
            return 'Minor'
        else:
            return 'Low'

    def _calculate_mttr(self) -> float:
        """
        Calculate Mean Time To Resolution
        
        Returns:
            MTTR in hours
        """
        durations = []
        
        for incident in self.incident_data:
            duration = incident['duration']
            if duration != "Unknown":
                # Extract hours from duration string
                if 'day' in duration:
                    hours = float(re.findall(r'\d+', duration)[0]) * 24
                elif 'hour' in duration:
                    hours = float(re.findall(r'\d+', duration)[0])
                elif 'minute' in duration:
                    hours = float(re.findall(r'\d+', duration)[0]) / 60
                else:
                    continue
                    
                durations.append(hours)
                
        return sum(durations) / len(durations) if durations else 0

    def _identify_key_issues(self) -> List[Dict[str, Any]]:
        """
        Identify key issues based on frequency and severity
        
        Returns:
            List of key issues
        """
        # Group similar incidents
        issue_groups = defaultdict(list)
        
        for incident in self.incident_data:
            # Create a simplified key for grouping
            key_words = set(re.findall(r'\w+', incident['title'].lower()))
            
            # Find the most similar existing group or create new
            max_similarity = 0
            best_match = None
            
            for existing_key in issue_groups.keys():
                similarity = len(key_words.intersection(existing_key)) / len(key_words.union(existing_key))
                if similarity > 0.5 and similarity > max_similarity:
                    max_similarity = similarity
                    best_match = existing_key
                    
            if best_match:
                issue_groups[best_match].append(incident)
            else:
                issue_groups[frozenset(key_words)].append(incident)
                
        # Identify key issues
        key_issues = []
        for group in issue_groups.values():
            if len(group) >= 2:  # Consider issues that occurred multiple times
                key_issues.append({
                    'title': group[0]['title'],
                    'frequency': len(group),
                    'category': self._categorize_incident(group[0]),
                    'severity': self._determine_severity(group[0]),
                    'last_occurrence': max(incident['date'] for incident in group)
                })
                
        # Sort by frequency and severity
        return sorted(key_issues, 
                     key=lambda x: (x['frequency'], 
                                  {'Critical': 4, 'Major': 3, 'Minor': 2, 'Low': 1}[x['severity']]),
                     reverse=True) 