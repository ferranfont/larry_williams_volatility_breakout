# Claude Code Configuration

This file contains configuration and commands for Claude Code to better assist with this project.

## Project Information
- **Project Type**: Complete algorithmic trading system
- **Strategy**: Larry Williams Volatility Breakout
- **Language**: Python 3.x
- **Main Focus**: Order management, visualization, and performance analysis
- **Data**: ES futures 1-minute data
- **Status**: ✅ Production ready

## Common Commands

### Essential 3-Step Workflow
```bash
# 1. Process raw data (first time only)
python main.py

# 2. Run trading strategy
cd strat_OM
python main_strat.py

# 3. Analyze results
cd strat_OM
python summary.py
```

### Configuration Workflow
```bash
# 1. Edit main_strat.py: Set start_date, end_date, dow_filter
# 2. Execute: python main_strat.py
# 3. Edit summary.py: Set target_filename to specific CSV
# 4. Execute: python summary.py
```

### Data Processing
```bash
# Process raw data and calculate trading levels
python main.py

# Generate daily data with range calculations
python main.py
```

### Testing and Development
```bash
# Install dependencies
pip install pandas numpy plotly

# Run individual modules for testing
python strat_OM/order_management.py
python quant_stat/range_calculations.py
python utils/date_utils.py
```

## Project Architecture

### Core System Components
- **strat_OM/**: Complete order management system
  - `main_strat.py` - Main execution engine
  - `order_management.py` - Trading logic and signal processing
  - `plot_chart_subset.py` - Interactive Plotly visualizations
  - `summary.py` - Performance analysis and HTML reports
  - `create_2022_subset.py` - Data subset generation

### Supporting Modules
- **quant_stat/**: Statistical calculations
  - `range_calculations.py` - Core range and volatility metrics
  - `get_levels.py` - Daily trading level calculations
- **utils/**: Utility functions
  - `date_utils.py` - Date processing and day-of-week functionality

### Data Management
- **data/**: All market data and results
  - `es_1min_data.csv` - Raw 1-minute ES futures data
  - `es_1D_data_range.csv` - Daily data with trading levels
  - `tracking_record_*.csv` - Trading results and performance
- **charts/**: Generated HTML visualizations

## Key Parameters

### Trading Configuration (main_strat.py)
- `start_date = '2024-08-15'` - Backtest start date
- `end_date = '2025-04-13'` - Backtest end date
- `dow_filter = 0` - Day filter (0=all days, 1=Monday, 2=Tuesday, etc.)

### Strategy Parameters (main.py)
- `expansion_pct = 0.4` - Range expansion for entry levels
- `stop_multiplier_pct = 2.5` - Stop loss distance multiplier
- `range_lookback = 3` - Lookback period for range calculations

### Analysis Configuration (summary.py)
- `target_filename = 'tracking_record_20240815_20250413.csv'` - Specific file to analyze

### File Naming Conventions
- Tracking records: `tracking_record_YYYYMMDD_YYYYMMDD.csv`
- Charts: `close_vol_chart_ES_1min_[suffix].html`
- Reports: `strategy_ratios_YYYYMMDD_YYYYMMDD.html`

## Development Workflow

### For Strategy Modifications
1. Modify parameters in `main_strat.py`
2. Run `python main_strat.py` to execute complete system
3. Analyze results with `python summary.py`
4. Review HTML charts and performance metrics

### For Data Updates
1. Update raw data in `data/es_1min_data.csv`
2. Run `python main.py` to recalculate daily levels
3. Execute trading system with updated data

### For Visualization Changes
1. Modify chart settings in `plot_chart_subset.py`
2. Re-run `main_strat.py` to regenerate charts
3. Check `charts/` directory for updated HTML files

## Performance Analysis Features

### Automated Reports
- **Console output**: Real-time progress and final statistics
- **HTML ratios table**: Professional performance metrics with color coding
- **Equity curve**: Green area chart showing cumulative P&L
- **Performance dashboard**: Monthly returns, trade distribution, rolling metrics

### Key Metrics Tracked
- Win rate, profit factor, Sharpe/Sortino/Calmar ratios
- Maximum drawdown and recovery analysis
- Trade duration and time-in-market statistics
- Monthly and daily performance breakdowns

## Visualization System

### Chart Types Generated
1. **Trading charts**: Price action with entry/exit points
   - Green circles: BUY entries
   - Red circles: SELL entries
   - Black squares: Exit points
   - Dotted lines: Trade connections

2. **Performance charts**: Equity curve and analysis
3. **HTML tables**: Complete performance metrics

### Chart Features
- Interactive Plotly charts with zoom/pan
- Range breaks to eliminate weekend gaps
- Transparent trading levels overlay
- Volume subplot integration

## Data Requirements

### Input Data Format
- CSV with columns: date, open, high, low, close, volume
- UTC timezone for all timestamps
- 1-minute resolution for ES futures
- Continuous contract data recommended

### Output Data Generated
- Daily trading levels with range calculations
- Complete trade records with entry/exit details
- Performance metrics and risk analysis
- Interactive HTML visualizations

## Notes for Claude Code

### When Making Modifications
- Always test changes with `main_strat.py` first
- Check console output for errors or warnings
- Verify HTML charts generate correctly in `charts/` directory
- Review tracking record CSV for data integrity

### Common Issues to Watch
- Date/timezone handling in pandas DataFrames
- Data type consistency (float vs object) in trading levels
- File path handling across different modules
- Memory usage with large datasets

### Performance Considerations
- Current system handles 87K+ records efficiently
- Visualization generation is the primary bottleneck
- HTML file sizes can be large with extensive data
- Consider data chunking for multi-year backtests

### Code Style Guidelines
- Use pandas for all data manipulation
- Plotly for all visualizations
- Clear function documentation with Parameters/Returns
- Consistent error handling and data validation