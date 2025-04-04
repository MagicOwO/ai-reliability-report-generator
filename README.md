# AI Reliability Report Generator

This project is an automated tool for analyzing service status pages of enterprise SaaS companies, generating reliability reports and peer comparisons.

## Features

- Scrapes and analyzes status page history data from multiple companies
- Generates detailed reliability reports including trend analysis and key issues
- Creates spreadsheets with detailed incident information
- Implements an incident categorization system based on peer analysis
- **AI-powered analysis for intelligent categorization and deeper insights**

## Prerequisites

- Docker and Docker Compose
- Or Python 3.9+ if running locally
- OpenAI API key for AI-powered analysis (highly recommended for best results)

## Installation and Setup

First, clone the repository:
```bash
git clone [repository-url]
cd report_gen
```

### Option 1: Using Docker (Recommended)
*Note: Please update the numpy version to 2.0.2 in the file requirements.txt to make Docker compatible with numpy.*

Build and run using Docker Compose:
```bash
docker-compose up --build
```

This is the most recommended way because it will automatically run everything:
- Install all dependencies 
- Install Playwright browsers
- Run the report generator and get final results

### Option 2: Local Installation

#### A. Automated Setup (Recommended)

Run the automated setup script:

**On Windows:**
```
.\setup.bat
```

**On Unix or MacOS:**
```bash
chmod +x setup.sh  # Make the script executable (first time only)
./setup.sh
```

The setup script will:
- Create a virtual environment if one doesn't exist
- Install all dependencies from requirements.txt
- Install browser binaries required by Playwright
- Activate the virtual environment
- Offer to run the report generator immediately

Everything is handled in a single command - no need to run multiple scripts or manually activate the environment!

#### B. Manual Setup

1. Create a virtual environment:
```bash
# On Windows:
python -m venv .venv

# On Unix or MacOS:
python3 -m venv .venv
```

2. Activate the virtual environment:
```bash
# On Windows (Command Prompt):
.\.venv\Scripts\activate

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On Unix or MacOS:
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

### Running the Report Generator

If you used the automated setup script, it will offer to run the report generator immediately after installation.

To run the report generator later:

1. **If using a local installation**, make sure your virtual environment is activated:
   ```bash
   # On Windows:
   .\.venv\Scripts\activate

   # On Unix or MacOS:
   source .venv/bin/activate
   ```

2. Run with one of these commands:
   ```bash
   # Basic usage (uses default OpenAI key)
   python -m src.report_generator

   # With explicit API key
   python -m src.report_generator --api-key=your_openai_api_key

   # Or set environment variable first
   export OPENAI_API_KEY=your_openai_api_key
   python -m src.report_generator
   ```

### Output

**Reports will be generated in the `./reports` directory with suffix `-report`, based on your configuration in `config/default_config.yaml`. The markdown file is report and xlsx file lists all the incidents from the target company.**

## AI-Powered Analysis

The report generator features integrated AI-powered analysis that enhances the basic report with:

1. **Intelligent Categorization:** Categorizes incidents into meaningful groups based on their nature and impact
2. **Root Cause Analysis:** Attempts to identify the underlying causes of incidents
3. **Severity Assessment:** Assigns severity levels to incidents based on their impact
4. **Duration Estimation:** Estimates incident duration where not explicitly stated
5. **Key Issue Identification:** Identifies recurring problems and patterns across incidents
6. **Trend Analysis:** Detects trends in incident frequency and types
7. **Comparative Analysis:** Compares the target company with peers to identify unique strengths and challenges

### AI Analysis Architecture

The AI analysis feature is built around the following components:

1. **AIIncidentAnalyzer**: Core class that interfaces with OpenAI's API to analyze incidents
   - Processes both target and peer incidents
   - Provides structured JSON output with categories, key issues, and trends
   - Updates original incident data with AI-generated categorizations

2. **Integration with Report Generation**: The AI analysis is seamlessly integrated into the report generation process
   - Standard analysis runs first to provide baseline metrics
   - AI analysis enhances these metrics with deeper insights when API key is available
   - Excel report automatically includes AI-powered sheets when analysis is available

3. **Fallback Mechanism**: If the API key is missing or AI analysis fails, the system gracefully falls back to standard analysis
   - Users always get a report, even without AI capabilities
   - Logging provides clear information about AI analysis status


### AI Analysis Output

When AI analysis is enabled, the report includes:

- Enhanced categorization with detailed descriptions of each category
- Key issues identified with impact assessment
- Comparative analysis between the target company and peers
- More accurate severity and duration information
- Detailed summary of reliability status

The analysis is also saved as a JSON file in the reports directory for further processing.

## Configuration

Edit `config/default_config.yaml` to configure:
- Target company and status page URL
- Peer companies and their status pages
- Analysis timeframe
- Scraping settings
- Analysis parameters
- Output settings

Example configuration:
```yaml
target_company:
  name: "New Relic"
  status_url: "https://status.newrelic.com/history"

peer_companies:
  - name: "MongoDB"
    status_url: "https://status.mongodb.com/history"
  # Add more peer companies...

timeframe:
  start_date: "2024-01-01"
  end_date: "2024-03-15"
```

## Design Overview

The AI Reliability Report Generator is built with a modular, extensible architecture that emphasizes asynchronous processing, data-driven analysis, and AI-enhanced insights. Below is a detailed breakdown of the system's design:

### 1. Core Architecture

#### a. Module Structure
The system follows a modular design pattern with clear separation of concerns:
- **Scrapers**: Handle data collection from different status pages
- **Analyzers**: Process and interpret incident data
- **Report Generators**: Transform analysis results into readable formats
- **Main Coordinator**: Orchestrates the workflow and handles configuration

#### b. Dependency Injection
- Configuration and services are passed explicitly to components, reducing tight coupling
- Components receive their dependencies through constructors, making testing easier
- Each component can operate independently with appropriate inputs

#### c. Command Pattern
- Main execution flow uses a command pattern for clear workflow stages
- Each stage (fetch, analyze, report) operates as a discrete unit
- Allows for easy insertion of new processing steps or analyzers

### 2. Asynchronous Processing Framework

#### a. Fetch and Process Pipeline
- Uses `aiohttp` and `asyncio` for non-blocking HTTP requests
- Implements context managers for proper resource management (`__aenter__`, `__aexit__`)
- Concurrent scraping of multiple status pages reduces total processing time

#### b. Resource Management
- Connection pooling minimizes network overhead
- Implements graceful cleanup of resources even during exceptions
- Configurable retry mechanisms with exponential backoff for transient failures

#### c. Playwright Integration
- Uses Playwright's headless browser for JavaScript-heavy pages
- Handles modern web applications that don't work with simple HTTP requests
- Provides browser automation for complex status page interactions

### 3. Web Scraping Infrastructure

#### a. BaseScraper Abstract Class
- Defines common interface and functionality for all scrapers
- Implements template method pattern with hooks for specialization
- Handles browser initialization, page navigation, and content extraction

#### b. StatusPageScraper Implementation
- Specializes in parsing incident data from status pages
- Uses BeautifulSoup for HTML parsing with resilient selectors
- Extracts structured incident data (title, date, description, status)

#### c. Error Handling and Resilience
- Multiple retry attempts with increasing delays
- Detailed logging of scraping process for debugging
- Fallback mechanisms when expected page elements aren't found

### 4. Dual-layer Analysis System

#### a. IncidentAnalyzer (Rule-based)
- Implements keyword-based categorization using predefined category dictionaries
- Calculates statistical metrics (MTTR, incident frequency)
- Identifies trends and patterns using time-series grouping
- Groups similar incidents to identify recurring issues

#### b. AIIncidentAnalyzer (AI-enhanced)
- Interfaces with OpenAI's API for advanced natural language understanding
- Constructs specialized prompts for reliability-focused analysis
- Processes both target and peer company incidents for comparative insights
- Enhances incident data with AI-generated categorizations and root causes

#### c. Analysis Result Integration
- Results from both analyzers are combined for a comprehensive view
- AI analysis enhances but doesn't replace basic statistical metrics
- System gracefully degrades to statistical analysis if AI is unavailable

### 5. Data Management and Transformation

#### a. Incident Data Model
- Flexible dictionary-based data model for incidents
- Standardized format for consistent processing
- Attribute enrichment during the analysis pipeline

#### b. Pandas Integration
- Uses Pandas DataFrames for efficient data manipulation
- Facilitates complex filtering, grouping, and aggregation operations
- Streamlines transformation between in-memory data and output formats

#### c. Report Generation System
- Comprehensive Excel report generation with multiple sheets
- Markdown report generation for text-based insights
- Chart generation for visual data representation

### 6. Configuration Management

#### a. YAML-based Configuration
- External configuration via YAML files
- Sensible defaults with override capabilities
- Environment variable integration for sensitive values

#### b. Command-line Interface
- Argument parsing for runtime configuration
- API key handling with multiple fallback mechanisms
- Configuration validation and error reporting

### 7. Error Handling and Logging

#### a. Hierarchical Logging
- Detailed logging at multiple levels (DEBUG, INFO, WARNING, ERROR)
- Component-specific loggers for targeted troubleshooting
- Contextual error information with traceback preservation

#### b. Graceful Degradation
- System continues functioning with partial data or limited capabilities
- Clear error reporting when components fail
- Fallback mechanisms ensure report generation despite errors

This architecture balances flexibility, performance, and reliability while providing clear extension points for future enhancements. The modular design allows for incremental improvements and feature additions without disrupting existing functionality.

## Future Improvements

After analyzing the codebase, here are detailed opportunities for future enhancements:

### 1. Enhanced Web Scraping Capabilities

- **Multi-format Status Page Support**: Extend the scraper to support different status page formats beyond the current implementation. Currently, the scraper expects a specific HTML structure (using classes like 'incident-container'), but many companies use different formats.
  
- **Historical Data Pagination**: Implement support for paginated status history pages. The current implementation only scrapes the first page, but many status pages use pagination for historical incidents.

- **Concurrent Domain-Specific Scraping**: Develop specialized scrapers for specific status page providers (StatusPage.io, Status.io, etc.) that can extract richer metadata like affected components and detailed timelines.

- **Fallback Mechanisms**: Create a cascade of scraping methods that fall back to alternative approaches when the primary method fails, improving resilience against layout changes.

### 2. Advanced AI Analysis Features

- **Fine-tuned Models**: Develop domain-specific models fine-tuned on incident data to improve categorization accuracy and root cause analysis.

- **Cross-incident Pattern Recognition**: Implement time-series analysis to detect patterns across incidents over time that might indicate systemic issues.

- **Proactive Recommendation Engine**: Extend the AI analyzer to provide specific recommendations based on identified patterns and industry best practices.

- **Custom Prompt Engineering**: Create a more sophisticated prompt management system that can be adapted based on the specific industries and incident types being analyzed.

- **Multi-model Approach**: Implement a system that uses different AI models for different types of analysis (categorization, root cause analysis, trend detection) to optimize for specific tasks.

### 3. Data Storage and Historical Analysis

- **Time-series Database Integration**: Implement a proper database backend (like InfluxDB or TimescaleDB) to store incident data for long-term analysis.

- **Incremental Updates**: Add capability to update existing reports with new incidents rather than regenerating the entire report each time.

- **Historical Trend Analysis**: Build advanced analytics for year-over-year or quarter-over-quarter reliability trend comparison.

- **Data Versioning**: Implement versioning for incident data to track how categorizations and analyses evolve over time.

### 4. Enhanced Reporting and Visualization

- **Interactive Dashboard**: Create a web-based dashboard with interactive charts and filtering capabilities instead of static Excel reports.

- **Customizable Report Templates**: Add support for user-defined report templates to meet different stakeholder needs.

- **Natural Language Summaries**: Generate contextual natural language summaries at different levels of detail for executives, engineers, and other stakeholders.

- **Comparative Benchmarking**: Enhance peer comparison to include industry benchmarks and statistical significance measurements.

- **Automated Insights**: Implement automated detection of statistically significant shifts in reliability metrics with smart alerting.

### 5. Architecture and Performance Optimizations

- **Caching Layer**: Implement an intelligent caching system for scraped data to reduce redundant API calls and improve performance.

- **Microservices Architecture**: Refactor the monolithic design into microservices (scraping service, analysis service, reporting service) to enable independent scaling.

- **Queue-based Processing**: Implement a job queue for handling large batches of companies or long time periods asynchronously.

- **Container Orchestration**: Enhance Docker implementation with proper orchestration to handle scaling for enterprise usage.

- **API Interface**: Develop a RESTful API to allow integration with other tools and systems.

### 6. User Experience Improvements

- **Configuration UI**: Create a web interface for managing configurations instead of editing YAML files.

- **Scheduled Reports**: Add capability to schedule regular report generation and distribution.

- **Alert Integration**: Integrate with popular alerting platforms (PagerDuty, OpsGenie, etc.) to correlate external alerts with observed incidents.

- **Multi-tenant Support**: Enhance the system to support multiple users with different permissions and report access controls.

Implementation of these improvements would transform the tool from a basic report generator into a comprehensive reliability intelligence platform suitable for enterprise use.

## Project Structure

```
reliability-report-generator/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── report_generator.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   └── status_page_scraper.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── incident_analyzer.py
│   │   ├── ai_analyzer.py
│   │   └── category_analyzer.py
│   └── utils/
│       ├── __init__.py
│       ├── excel_generator.py
│       └── config_loader.py
├── config/
│   └── default_config.yaml
└── reports/
    └── .gitkeep
```