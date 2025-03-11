import json
from pathlib import Path

# Placeholder for actual LLM integration
# In a real implementation, this would use OpenAI, Mistral, or another LLM API

def generate_business_insights(financial_data, business_type="hotel"):
    """
    Generate business insights based on financial data using an LLM
    
    Parameters:
    -----------
    financial_data : pandas.DataFrame
        Processed financial data
    business_type : str
        Type of business (default: hotel)
    
    Returns:
    --------
    dict
        Dictionary containing insights and recommendations
    """
    # In a real implementation, this would call an LLM API
    # For now, we'll return predefined insights based on the data
    
    insights = {
        "summary": "Analysis of your hotel's financial performance",
        "insights": [],
        "recommendations": []
    }
    
    # Calculate some basic metrics to generate insights
    if len(financial_data) > 1:
        # Revenue trend
        revenue_trend = financial_data['revenue'].pct_change().mean() * 100
        if revenue_trend > 0:
            insights["insights"].append(f"Your revenue is showing a positive trend, growing at approximately {revenue_trend:.1f}% month-over-month.")
        else:
            insights["insights"].append(f"Your revenue is showing a negative trend, declining at approximately {abs(revenue_trend):.1f}% month-over-month.")
        
        # Profit margin analysis
        avg_profit_margin = financial_data['profit_margin'].mean() * 100
        insights["insights"].append(f"Your average profit margin is {avg_profit_margin:.1f}%, which is {'above' if avg_profit_margin > 30 else 'below'} the industry average for hotels.")
        
        # Seasonality detection
        if 'date' in financial_data.columns and len(financial_data) >= 12:
            financial_data['month'] = financial_data['date'].dt.month
            monthly_avg = financial_data.groupby('month')['revenue'].mean()
            peak_month = monthly_avg.idxmax()
            low_month = monthly_avg.idxmin()
            month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 
                          7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
            
            insights["insights"].append(f"Your peak revenue month appears to be {month_names[peak_month]}, while your lowest revenue month is {month_names[low_month]}.")
            
            # Seasonal recommendations
            if peak_month in [6, 7, 8]:  # Summer months
                insights["recommendations"].append("Consider implementing dynamic pricing strategies during your peak summer months to maximize revenue.")
            if low_month in [1, 2, 11, 12]:  # Winter months
                insights["recommendations"].append("Your hotel experiences lower occupancy during winter months. Consider creating special winter packages or events to attract guests during this off-peak period.")
    
    # Cost structure analysis
    if 'cost_category' in financial_data.columns and 'cost' in financial_data.columns:
        cost_by_category = financial_data.groupby('cost_category')['cost'].sum()
        highest_cost = cost_by_category.idxmax()
        highest_cost_pct = (cost_by_category.max() / cost_by_category.sum()) * 100
        
        insights["insights"].append(f"Your highest cost category is '{highest_cost}', representing {highest_cost_pct:.1f}% of your total costs.")
        
        if highest_cost == 'Energy' and highest_cost_pct > 15:
            insights["recommendations"].append("Your energy costs are higher than the industry average. Consider investing in energy-efficient solutions to reduce operational costs.")
        elif highest_cost == 'Staff' and highest_cost_pct > 40:
            insights["recommendations"].append("Staff costs represent a significant portion of your expenses. Review staffing levels during off-peak periods and consider cross-training employees for multiple roles.")
    
    # Revenue stream analysis
    if 'revenue_category' in financial_data.columns and 'revenue' in financial_data.columns:
        revenue_by_category = financial_data.groupby('revenue_category')['revenue'].sum()
        highest_revenue = revenue_by_category.idxmax()
        highest_revenue_pct = (revenue_by_category.max() / revenue_by_category.sum()) * 100
        
        insights["insights"].append(f"Your highest revenue category is '{highest_revenue}', representing {highest_revenue_pct:.1f}% of your total revenue.")
        
        if highest_revenue == 'Rooms' and highest_revenue_pct > 70:
            insights["recommendations"].append("Your business is heavily dependent on room revenue. Consider developing additional revenue streams such as spa services, premium dining experiences, or event hosting.")
        elif highest_revenue == 'Food & Beverage' and highest_revenue_pct > 30:
            insights["recommendations"].append("Your food and beverage operations are performing well. Consider expanding this service with special dining events or themed nights to attract local customers as well as hotel guests.")
    
    # Add generic hotel recommendations
    insights["recommendations"].extend([
        "Implement a customer relationship management (CRM) system to track guest preferences and enhance personalized service.",
        "Review your online presence and booking channels to ensure maximum visibility and competitive pricing.",
        "Consider sustainability initiatives that can both reduce costs and appeal to environmentally conscious travelers."
    ])
    
    return insights

def save_insights(insights, filename="business_insights.json"):
    """
    Save generated insights to a file
    
    Parameters:
    -----------
    insights : dict
        Dictionary containing insights and recommendations
    filename : str
        Name of the file to save insights to
    """
    # Create reports directory if it doesn't exist
    reports_dir = Path("data/reports")
    reports_dir.mkdir(exist_ok=True, parents=True)
    
    # Save insights to file
    with open(reports_dir / filename, 'w') as f:
        json.dump(insights, f, indent=4)
    
    return str(reports_dir / filename)
