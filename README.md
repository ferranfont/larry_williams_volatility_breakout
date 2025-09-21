# Larry Williams Volatility Breakout Strategy

A comprehensive Python implementation of the Larry Williams Volatility Breakout trading strategy with advanced order management, performance analysis, and visualization capabilities.

## Overview

This project implements a complete trading system based on the Larry Williams Volatility Breakout strategy, featuring:
- Automated range calculations and trading levels
- Order management with entry/exit logic
- Interactive visualization with Plotly
- Comprehensive performance analysis and risk metrics

## Features

### 🎯 Trading Strategy
- **Range-based breakout detection** with configurable parameters
- **Daily level calculations** (long/short levels and stops)
- **First crossover detection** (only one signal per day per direction)
- **Stop loss and end-of-day exit management**
- **Trade tracking and performance metrics**

### 📊 Visualization
- **Interactive Plotly charts** with price action, volume, and trading levels
- **Entry/exit point visualization** (green/red circles for entries, black squares for exits)
- **Connection lines** showing complete trade lifecycle
- **Range breaks** to eliminate weekend gaps

### 📈 Performance Analysis
- **Comprehensive strategy summary** with 25+ metrics
- **Risk-adjusted ratios** (Sharpe, Sortino, Calmar)
- **Drawdown analysis** and equity curve visualization
- **HTML reports** with professional formatting
- **Monthly returns and trade distribution analysis**

## Installation

```bash
pip install pandas numpy plotly
```

## Quick Start - 3 Simple Steps

### 1. Process Raw Data (First Time Only)
```bash
python main.py
```
- Processes raw ES futures data
- Calculates daily trading levels
- Creates base data files

### 2. Run Trading Strategy
```bash
cd strat_OM
python main_strat.py
```
- Configure dates and filters in the file
- Executes complete trading system
- Generates charts and CSV results

### 3. Analyze Performance
```bash
cd strat_OM
python summary.py
```
- Edit `target_filename` in the file to specify which results to analyze
- Generates HTML reports and equity curves
- Opens analysis in browser automatically

## Strategy Parameters

### Core Parameters (configurable in main.py)
- `expansion_pct = 0.4` - Range expansion factor for entry levels
- `stop_multiplier_pct = 0.5` - Stop loss distance multiplier
- `range_lookback = 3` - Lookback period for range calculations

### Trading Rules
1. **Entry Signals**: First crossover above long level (BUY) or below short level (SELL)
2. **Exit Conditions**: Stop loss hit OR end of trading day
3. **Position Management**: Maximum one trade per direction per day
4. **Risk Management**: Fixed stop levels based on previous day's range

## Project Structure

```
larry_williams_volatility_breakout/
├── README.md
├── CLAUDE.md                          # Claude Code configuration
├── main.py                            # Initial strategy and data processing
├── data/                              # Market data and results
│   ├── es_1min_data.csv              # Raw 1-minute ES futures data
│   ├── es_1D_data_range.csv          # Daily data with trading levels
│   └── tracking_record_*.csv         # Trading results
├── strat_OM/                         # Order Management System
│   ├── main_strat.py                 # Main trading system executor
│   ├── create_2022_subset.py         # Data subset creation
│   ├── order_management.py           # Trade execution logic
│   ├── plot_chart_subset.py          # Interactive visualization
│   └── summary.py                    # Performance analysis & reports
├── quant_stat/                       # Statistical calculations
│   ├── range_calculations.py         # Range and indicator calculations
│   └── get_levels.py                 # Trading level calculations
├── utils/                            # Utility functions
│   └── date_utils.py                 # Date and time utilities
└── charts/                           # Generated HTML charts
    ├── equity_curve_*.html           # Equity curve visualization
    ├── strategy_ratios_*.html        # Performance metrics table
    └── close_vol_chart_*.html        # Trading charts
```

## Key Outputs

### 1. Trading Charts
- **Price action** with volume overlay
- **Trading levels** (transparent green/red lines)
- **Entry points** (green circles for BUY, red circles for SELL)
- **Exit points** (black squares)
- **Trade connections** (dotted grey lines)

### 2. Performance Reports
- **Console summary** with key metrics
- **HTML ratios table** with color-coded performance indicators
- **Equity curve** (green area chart showing cumulative P&L)
- **Performance dashboard** with monthly returns and trade analysis

### 3. Trading Results
- **CSV tracking records** with complete trade details
- **Win rate, profit factor, and risk metrics**
- **Drawdown analysis and time-in-market statistics**

## Strategy Performance Metrics

### Basic Statistics
- Total trades, win rate, average trade P&L
- Maximum winning/losing streaks
- Time in market analysis

### Risk-Adjusted Ratios
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk-adjusted returns
- **Calmar Ratio**: Annual return / Maximum drawdown
- **Profit Factor**: Gross profit / Gross loss

### Drawdown Analysis
- Maximum drawdown (absolute and percentage)
- Drawdown duration and recovery analysis

## Data Requirements

- **ES futures 1-minute data** in CSV format with columns: date, open, high, low, close, volume
- **UTC timezone** for all timestamps
- **Continuous contract** data recommended for backtesting

## Summary

### Essential Files Overview

#### **Core Trading System**
- **`strat_OM/main_strat.py`** - Main execution engine that runs the complete trading workflow
  - Loads data subsets for specified date ranges
  - Executes order management system
  - Generates interactive charts with trade visualization
  - Saves trading results to CSV files
  - Primary entry point for running the strategy

- **`strat_OM/order_management.py`** - Core trading logic and signal processing
  - Implements Larry Williams breakout detection algorithm
  - Manages entry/exit signals with first-crossover-only logic
  - Handles stop loss and end-of-day exit conditions
  - Tracks trade performance and calculates metrics
  - Returns both trade records and enriched price data

#### **Data Processing**
- **`main.py`** - Initial data processor and range calculator
  - Processes raw 1-minute ES futures data
  - Calculates daily ranges and volatility indicators
  - Generates trading levels (long/short entry and stop levels)
  - Creates the foundation daily data file
  - Sets up the core parameters (expansion_pct=0.4, stop_multiplier_pct=0.5)

- **`strat_OM/create_2022_subset.py`** - Data subset generator
  - Creates filtered datasets for specific date ranges
  - Removes Sunday trading data for cleaner analysis
  - Merges 1-minute data with daily trading levels
  - Converts data types for optimal performance
  - Essential for backtesting specific periods

#### **Analysis & Visualization**
- **`strat_OM/summary.py`** - Comprehensive performance analysis engine
  - Generates 25+ performance metrics and risk ratios
  - Creates professional HTML reports with color-coded tables
  - Produces equity curve visualization (green area chart)
  - Calculates Sharpe, Sortino, Calmar ratios and drawdown analysis
  - Automatically opens results in browser for easy review

- **`strat_OM/plot_chart_subset.py`** - Interactive chart generator
  - Creates Plotly charts with price action and volume
  - Visualizes trading levels as transparent horizontal lines
  - Shows entry points (green/red circles) and exit points (black squares)
  - Connects trades with dotted lines showing complete lifecycle
  - Implements range breaks to eliminate weekend gaps

#### **Supporting Calculations**
- **`quant_stat/range_calculations.py`** - Statistical calculation engine
  - Computes daily ranges and rolling averages
  - Calculates entry and stop levels based on volatility
  - Implements configurable lookback periods
  - Core mathematical foundation for the strategy

- **`quant_stat/get_levels.py`** - Trading level calculator
  - Determines long/short entry levels using next day's open + previous range
  - Calculates stop loss levels for risk management
  - Applies expansion factors to create breakout thresholds
  - Links volatility calculations to actual trading signals

#### **Utility Functions**
- **`utils/date_utils.py`** - Date processing utilities
  - Adds day-of-week functionality for filtering
  - Handles timezone conversions and date formatting
  - Supports Sunday data removal for cleaner backtests
  - Essential for proper time-based analysis

### Quick Start Workflow
1. **Data Setup**: Run `python main.py` to process raw data and calculate trading levels
2. **Execute Strategy**: Run `python strat_OM/main_strat.py` to backtest and generate charts
3. **Analyze Results**: Run `python strat_OM/summary.py` for comprehensive performance analysis
4. **Review Outputs**: Check `charts/` for HTML visualizations and `data/` for CSV results

## Configuration

All parameters can be modified in the respective files:
- **Trading parameters**: `main.py` and `main_strat.py`
- **Date ranges**: `main_strat.py` (start_date, end_date)
- **Visualization settings**: `plot_chart_subset.py`

## Contributing

This project follows professional coding standards with:
- Modular architecture for easy testing and modification
- Comprehensive documentation and error handling
- Type hints and clear function interfaces
- Separate concerns (data processing, trading logic, visualization)

## Contact

ferran@orderbooktrading.com

