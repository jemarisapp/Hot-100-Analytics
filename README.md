# Billboard Hot 100 Data Analytics Project

## Overview

This project is a comprehensive data analytics system for tracking and visualizing Billboard Hot 100 chart performance. It combines a **SQLite database** for data storage, **Python scripts** for data processing, and **Power BI** for interactive visualizations and dashboards.

**The Challenge:** Music industry executives and fans struggle to understand cross-platform performance dynamics in today's fragmented landscape.  Traditional chart rankings present data in ways that make cross-platform analysis difficult - single ranking numbers don't show what drives success, and separate charts for streams/airplay/sales exist but aren't easily compared.

**The Solution:** This dashboard transforms fragmented Billboard data into strategic intelligence by consolidating streams, airplay, and sales into unified views that reveal why songs succeed on different platforms. Instead of separate charts that require manual correlation, executives can instantly see how streaming dominance, radio reach, and sales patterns combine to create chart success.

The system tracks detailed metrics including:
- **Billboard Rankings** and position changes
- **Streaming Data** (total streams and market share)
- **Airplay Performance** (radio airplay metrics)
- **Sales Figures** (digital and physical sales)
- **Total Units** (combined consumption metrics)
- **Chart Performance** (weeks on chart, peak positions)

## Project Architecture

### 1. Data Storage Layer
- **SQLite Database** (`charts.db`) - Central data repository
- **CSV Files** - Weekly chart data imports and reference data
- **Database Schema**:
  - `artists` - Artist information and metadata
  - `songs` - Song titles and basic information
  - `song_artists` - Many-to-many relationship between songs and artists
  - `chart_weeks` - Weekly chart periods and metadata
  - `chart_entries` - Individual chart entries with performance metrics

### 2. Data Processing Layer
- **Python Scripts** (`Scripts/quick_db_loader.py`) - Automated data loading and processing
- **Artist Name Standardization** - Intelligent parsing of collaborative artist names
- **Data Validation** - Format checking and error handling
- **Batch Processing** - Support for weekly chart updates

### 3. Visualization Layer
- **Power BI Dashboard** (`Hot100 Dashboard.pbix`) - Interactive analytics interface
- **DAX Measures** - Advanced calculations and rankings
- **Multi-dimensional Views** - Points, streaming, airplay, and sales analysis

## How It Was Built

### Phase 1: Database Design
The project began with designing a normalized database schema to handle the complex relationships between artists, songs, and chart performance data. The SQLite database was chosen for its simplicity, portability, and Python integration.

### Phase 2: Data Processing Engine
A Python-based data loader was developed to:
- Parse weekly chart CSV files
- Automatically split collaborative artist names (e.g., "Artist A, Artist B & Artist C")
- Handle various data formats (K, M, B suffixes for numbers)
- Validate data integrity
- Support both insert and update operations

### Phase 3: Power BI Integration
The visualization layer was built using Power BI with:
- **Custom DAX measures** for ranking calculations
- **Dynamic filtering** by week, artist, and song
- **Multi-panel dashboard** showing different performance metrics
- **Interactive charts** for trend analysis

### Phase 4: Data Management
Reference files and weekly chart imports were organized to support:
- **Standardized artist names** across different data sources
- **Weekly chart updates** with minimal manual intervention
- **Data consistency** through automated validation

## Key Features

### 🎯 **Intelligent Artist Parsing**
- Automatically detects and splits collaborative artist names
- Handles various separators: `,`, `&`, `feat./ft.`, `x`, `and`, `with`
- Protects special cases like "Tyler, The Creator"

### 📊 **Comprehensive Metrics Tracking**
- **Billboard Ranking**: Position on the Hot 100 chart
- **Streaming Performance**: Total streams and market share percentage
- **Airplay Metrics**: Radio airplay data and rankings
- **Sales Figures**: Digital and physical sales performance
- **Total Units**: Combined consumption metrics

### 🔄 **Automated Data Updates**
- Weekly chart imports via CSV files
- Upsert operations (insert new, update existing)
- Data validation and error handling
- Batch processing capabilities

### 📈 **Advanced Analytics**
- **Multi-dimensional Rankings**: Separate rankings for each metric type
- **Performance Trends**: Week-over-week changes and peak positions
- **Market Share Analysis**: Percentage breakdowns across metrics
- **Comparative Analysis**: Cross-song and cross-week comparisons

## Data Sources

### Weekly Chart Data
- **Format**: CSV files with standardized headers
- **Frequency**: Weekly updates
- **Source**: Billboard Hot 100 chart data
- **Fields**: Rank, position change, song, artist, points, streams, airplay, sales, units

### Reference Data
- **Artists Reference**: Standardized artist names and aliases
- **Songs Reference**: Song title variations and metadata
- **Database Exports**: CSV backups of database tables

## Usage Instructions

### Adding New Weekly Data
1. **Prepare CSV file** with the required header format
2. **Run the loader script**:
   ```powershell
   python .\Scripts\quick_db_loader.py --db .\charts.db --week 2025-08-23 --chart "Week of August 23rd" --csv .\weekly_charts\add_2025-08-23.csv --mode replace
   ```

### Updating Existing Data
- Use the same command with `--mode replace` to update existing entries
- The system will upsert based on week and rank combinations

### Viewing Analytics
- Open `.pbix` in Power BI
- Use filters to select specific weeks, artists, or songs
- Explore different metric views and rankings

## Technical Specifications

### Database
- **Type**: SQLite 3
- **Size**: ~80KB (compressed data)
- **Tables**: 5 main tables with optimized relationships
- **Indexing**: Primary keys on chart entries and relationships

### Python Scripts
- **Version**: Python 3.x compatible
- **Dependencies**: Standard library only (sqlite3, csv, re, argparse)
- **Performance**: Optimized for batch processing

### Power BI
- **Version**: Power BI Desktop
- **Data Source**: Direct SQLite connection
- **Measures**: 50+ custom DAX calculations
- **Visualizations**: 15+ interactive charts and tables

## Project Benefits

### For Music Industry Analysts
- **Real-time Performance Tracking**: Monitor chart movements and trends
- **Competitive Analysis**: Compare artist and song performance
- **Market Insights**: Understand streaming vs. airplay vs. sales dynamics

### For Data Scientists
- **Clean, Structured Data**: Well-normalized database schema
- **Automated Processing**: Minimal manual data entry required
- **Extensible Architecture**: Easy to add new metrics or data sources

### For Business Intelligence
- **Interactive Dashboards**: Self-service analytics capabilities
- **Historical Analysis**: Track performance over time
- **Custom Reporting**: Flexible DAX measures for specific needs

## Future Enhancements

### Planned Features
- **API Integration**: Real-time data feeds from Billboard
- **Machine Learning**: Predictive chart performance models
- **Social Media Integration**: Sentiment analysis correlation
- **Mobile Dashboard**: Responsive design for mobile devices

### Technical Improvements
- **Cloud Deployment**: Azure/AWS hosting for scalability
- **Real-time Updates**: Webhook-based data synchronization
- **Advanced Analytics**: Statistical analysis and forecasting tools

## Support and Maintenance

### Regular Tasks
- **Weekly Data Updates**: Import new chart data
- **Data Validation**: Check for anomalies or errors
- **Performance Monitoring**: Optimize database queries
- **Backup Management**: Regular database exports

### Troubleshooting
- **Common Issues**: Documented in `Scripts/MUSIC_CHARTS_DB_GUIDE.md`
- **Data Validation**: Built-in error checking and reporting
- **Performance Tuning**: Query optimization and indexing

---

**Project Status**: Active Development  
**Last Updated**: August 29, 2025  
**Data Coverage**: Billboard Hot 100 (Weekly)  
**Technology Stack**: SQLite, Python, Power BI, DAX  

*This project demonstrates how modern data analytics tools can transform traditional music industry data into actionable insights and interactive visualizations.*


