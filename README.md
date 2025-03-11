# Hotel Financial Dashboard & Business Planning

A Streamlit-based dashboard for financial reporting, budget planning, and business insights for hotels. This application allows users to upload financial data, visualize key metrics, generate budget forecasts, and receive AI-powered business insights.

## Features

- **Secure Authentication**: User login and registration system using Streamlit's new authentication capabilities
- **Data Upload**: Support for CSV and Excel file uploads containing financial data
- **Financial Analysis**: Interactive visualizations for revenue, costs, and profitability metrics
- **Budget Planning**: Generate budget forecasts with customizable growth rates and time periods
- **AI Business Insights**: Receive business recommendations based on your financial data (powered by LLM integration)
- **Hotel-Specific Metrics**: Focus on hotel industry KPIs and seasonal patterns

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hotel-financial-dashboard.git
   cd hotel-financial-dashboard
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

4. Access the dashboard in your web browser at `http://localhost:8501`

### Default Login

- Username: `admin`
- Password: `admin123`

## Data Format

The dashboard works best with financial data in the following format:

- Date column (monthly or quarterly periods)
- Revenue figures (total and/or by category)
- Cost figures (total and/or by category)
- EBITDA or profit figures

If your data doesn't exactly match this format, the application will attempt to adapt it automatically.

## Deployment

This application can be deployed to Streamlit Cloud for free:

1. Push your code to GitHub
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and point it to your GitHub repository
4. Configure the app to run `app.py`

## Project Structure

```
├── app/
│   └── main.py          # Main Streamlit application
├── database/            # User and token storage
├── utils/
│   ├── __init__.py
│   ├── authentication.py # Authentication functions
│   ├── data_processing.py # Data processing utilities
│   └── ai_insights.py    # AI integration for business insights
├── app.py               # Entry point for the application
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Future Enhancements

- Integration with more sophisticated forecasting models
- Expanded hotel-specific KPIs (RevPAR, ADR, Occupancy Rate)
- Customizable dashboard layouts
- Export options for reports and visualizations
- Multi-property comparison

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.