# AI-Powered Analysis

This document provides a detailed overview of the integrated AI analysis feature in the report generator.

## Overview

The AI analysis feature has now been integrated as a core component of the report generator, requiring no additional flags to enable. As long as a valid OpenAI API key is provided, the system will automatically utilize AI-enhanced analysis capabilities.

## Key Features

The AI analyzer offers the following enhancements:

1. **Intelligent Categorization**: Groups incidents into meaningful categories based on their nature and impact.
2. **Root Cause Analysis**: Attempts to identify the underlying causes of incidents.
3. **Severity Assessment**: Assigns severity levels to incidents based on their impact.
4. **Duration Estimation**: Estimates incident duration where not explicitly stated.
5. **Key Issue Identification**: Identifies recurring problems and patterns across incidents.
6. **Trend Analysis**: Detects trends in incident frequency and types.
7. **Comparative Analysis**: Compares the target company with peers to identify unique strengths and challenges.

## Technical Architecture

The AI analysis feature is built around the following components:

1. **AIIncidentAnalyzer**: The core class that interfaces with OpenAI's API to analyze incidents.
   - Processes both target and peer incidents.
   - Provides structured JSON output with categories, key issues, and trends.
   - Updates original incident data with AI-generated categorizations.

2. **Integration with Report Generation**: The AI analysis is seamlessly integrated into the report generation process.
   - Standard analysis runs first to provide baseline metrics.
   - AI analysis enhances these metrics with deeper insights when the API key is available.
   - The Excel report automatically includes AI-powered sheets when analysis is available.

3. **Fallback Mechanism**: If the API key is missing or AI analysis fails, the system gracefully falls back to standard analysis.
   - Users always receive a report, even without AI capabilities.
   - Logging provides clear information about the status of AI analysis.

## Using AI Analysis

To enable AI-powered analysis, you need to provide an OpenAI API key. There are three ways to do this:

1. **Command Line Parameter**: Pass the API key directly with the `--api-key` parameter:
```bash
python -m src.report_generator --api-key=your_openai_api_key
```

2. **Environment Variable**: Set the API key as the `OPENAI_API_KEY` environment variable:
```bash
export OPENAI_API_KEY=your_openai_api_key
python -m src.report_generator
```

3. **Default API Key** (recommended for development):
The system includes a default API key placeholder that you should replace with your actual key.
To set your API key as the default:

   1. Open the file `src/analyzers/ai_analyzer.py`
   2. Find the line with `DEFAULT_OPENAI_API_KEY = "sk-your-default-api-key-replace-this"`
   3. Replace the placeholder with your actual OpenAI API key

   This approach is most convenient for development as you won't need to provide the key with each command.

The system will use these sources in priority order: command line, environment variable, default key.

## AI Analysis Output

When AI analysis is enabled, the report includes:

- Enhanced categorization with detailed descriptions of each category.
- Key issues identified with impact assessments.
- Comparative analysis between the target company and peers.
- More accurate severity and duration information.
- Detailed summary of reliability status.

The analysis is also saved as a JSON file in the reports directory for further processing.

## Demo Script

To facilitate understanding of the AI analysis functionality, we provide a demo script: `demo_ai_analysis.py`. This script runs AI analysis using sample data, demonstrating its capabilities without needing to scrape websites.

Usage:
```bash
python demo_ai_analysis.py --api-key=your_openai_api_key
# Or use the environment variable
export OPENAI_API_KEY=your_openai_api_key
python demo_ai_analysis.py
# Or use the default API key you've set
python demo_ai_analysis.py
```

## Troubleshooting

If you encounter issues while using AI analysis, please check the following:

1. Ensure your OpenAI API key is valid and not expired.
2. Check your internet connection for stability.
3. Review the log output for detailed error information.
4. Ensure your API key has sufficient usage quota.

If problems persist, the system will automatically generate a report using standard analysis.