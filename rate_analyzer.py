"""
Rate analyzer module for analyzing contractor rates and billing data.

This module provides comprehensive analysis of contractor rates including
statistical analysis, trend detection, and comparative metrics.
"""

import logging
import statistics
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class RateData:
    """Data class for individual rate records."""
    contractor_id: str
    rate: float
    currency: str
    date: datetime
    project_type: str
    skill_level: str
    location: str
    hours_worked: Optional[float] = None
    overtime_rate: Optional[float] = None


@dataclass
class RateAnalysisResult:
    """Data class for rate analysis results."""
    total_records: int
    mean_rate: float
    median_rate: float
    std_deviation: float
    min_rate: float
    max_rate: float
    rate_range: float
    percentile_25: float
    percentile_75: float
    interquartile_range: float
    coefficient_of_variation: float
    analysis_date: datetime
    currency: str
    outliers: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary."""
        result = asdict(self)
        result['analysis_date'] = self.analysis_date.isoformat()
        return result


@dataclass
class TrendAnalysis:
    """Data class for rate trend analysis."""
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # -1.0 to 1.0
    average_change_per_month: float
    r_squared: float
    confidence_level: float
    prediction_next_month: float
    seasonal_patterns: Dict[str, float]


@dataclass
class ComparativeAnalysis:
    """Data class for comparative rate analysis."""
    by_project_type: Dict[str, Dict[str, float]]
    by_skill_level: Dict[str, Dict[str, float]]
    by_location: Dict[str, Dict[str, float]]
    by_time_period: Dict[str, Dict[str, float]]
    top_performers: List[Dict[str, Any]]
    bottom_performers: List[Dict[str, Any]]


class RateAnalyzer:
    """Main class for analyzing contractor rates."""
    
    def __init__(self, default_currency: str = 'USD'):
        """Initialize the rate analyzer.
        
        Args:
            default_currency: Default currency for analysis
        """
        self.default_currency = default_currency
        self.rate_data: List[RateData] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def add_rate_data(self, rate_data: Union[RateData, List[RateData]]) -> None:
        """Add rate data to the analyzer.
        
        Args:
            rate_data: Single rate data or list of rate data
        """
        if isinstance(rate_data, RateData):
            self.rate_data.append(rate_data)
        elif isinstance(rate_data, list):
            self.rate_data.extend(rate_data)
        else:
            raise ValueError("Invalid rate data type")
            
    def clear_data(self) -> None:
        """Clear all stored rate data."""
        self.rate_data.clear()
        
    def _validate_rate_data(self, data: List[RateData]) -> List[RateData]:
        """Validate and clean rate data.
        
        Args:
            data: List of rate data to validate
            
        Returns:
            List of validated rate data
        """
        validated_data = []
        
        for rate_record in data:
            if rate_record.rate <= 0:
                self.logger.warning(f"Invalid rate {rate_record.rate} for contractor {rate_record.contractor_id}")
                continue
                
            if not rate_record.contractor_id:
                self.logger.warning("Missing contractor ID")
                continue
                
            if not rate_record.currency:
                rate_record.currency = self.default_currency
                
            validated_data.append(rate_record)
            
        return validated_data
    
    def _detect_outliers(self, rates: List[float], threshold: float = 2.0) -> List[int]:
        """Detect outliers using z-score method.
        
        Args:
            rates: List of rates
            threshold: Z-score threshold for outlier detection
            
        Returns:
            List of indices of outliers
        """
        if len(rates) < 3:
            return []
            
        mean_rate = statistics.mean(rates)
        std_dev = statistics.stdev(rates)
        
        if std_dev == 0:
            return []
            
        outliers = []
        for i, rate in enumerate(rates):
            z_score = abs(rate - mean_rate) / std_dev
            if z_score > threshold:
                outliers.append(i)
                
        return outliers
    
    def analyze_rates(
        self, 
        data: Optional[List[RateData]] = None,
        include_outliers: bool = True,
        currency_filter: Optional[str] = None
    ) -> RateAnalysisResult:
        """Analyze contractor rates and return comprehensive statistics.
        
        Args:
            data: Optional rate data to analyze. If None, uses stored data
            include_outliers: Whether to include outliers in analysis
            currency_filter: Filter by specific currency
            
        Returns:
            RateAnalysisResult with comprehensive analysis
            
        Raises:
            ValueError: If no data available for analysis
        """
        analysis_data = data if data is not None else self.rate_data
        
        if not analysis_data:
            raise ValueError("No rate data available for analysis")
            
        # Validate and filter data
        validated_data = self._validate_rate_data(analysis_data)
        
        if currency_filter:
            validated_data = [d for d in validated_data if d.currency == currency_filter]
            
        if not validated_data:
            raise ValueError("No valid data after filtering")
            
        rates = [d.rate for d in validated_data]
        currency = validated_data[0].currency
        
        # Detect outliers
        outlier_indices = self._detect_outliers(rates)
        outlier_data = []
        
        for idx in outlier_indices:
            outlier_data.append({
                'contractor_id': validated_data[idx].contractor_id,
                'rate': validated_data[idx].rate,
                'date': validated_data[idx].date.isoformat(),
                'project_type': validated_data[idx].project_type,
                'z_score': abs(validated_data[idx].rate - statistics.mean(rates)) / statistics.stdev(rates)
            })
        
        # Remove outliers if requested
        if not include_outliers and outlier_indices:
            filtered_rates = [rate for i, rate in enumerate(rates) if i not in outlier_indices]
            if filtered_rates:
                rates = filtered_rates
        
        # Calculate statistics
        mean_rate = statistics.mean(rates)
        median_rate = statistics.median(rates)
        std_deviation = statistics.stdev(rates) if len(rates) > 1 else 0.0
        min_rate = min(rates)
        max_rate = max(rates)
        rate_range = max_rate - min_rate
        
        # Calculate percentiles
        sorted_rates = sorted(rates)
        n = len(sorted_rates)
        percentile_25 = sorted_rates[int(n * 0.25)] if n > 0 else 0
        percentile_75 = sorted_rates[int(n * 0.75)] if n > 0 else 0
        interquartile_range = percentile_75 - percentile_25
        
        # Calculate coefficient of variation
        coefficient_of_variation = (std_deviation / mean_rate) if mean_rate != 0 else 0
        
        return RateAnalysisResult(
            total_records=len(validated_data),
            mean_rate=round(mean_rate, 2),
            median_rate=round(median_rate, 2),
            std_deviation=round(std_deviation, 2),
            min_rate=min_rate,
            max_rate=max_rate,
            rate_range=round(rate_range, 2),
            percentile_25=percentile_25,
            percentile_75=percentile_75,
            interquartile_range=round(interquartile_range, 2),
            coefficient_of_variation=round(coefficient_of_variation, 4),
            analysis_date=datetime.now(),
            currency=currency,
            outliers=outlier_data
        )
    
    def analyze_trends(
        self, 
        data: Optional[List[RateData]] = None,
        time_period_months: int = 12
    ) -> TrendAnalysis:
        """Analyze rate trends over time.
        
        Args:
            data: Optional rate data to analyze
            time_period_months: Number of months to analyze
            
        Returns:
            TrendAnalysis with trend information
        """
        analysis_data = data if data is not None else self.rate_data
        
        if not analysis_data:
            raise ValueError("No rate data available for trend analysis")
            
        validated_data = self._validate_rate_data(analysis_data)
        
        # Filter by time period
        cutoff_date = datetime.now() - timedelta(days=time_period_months * 30)
        recent_data = [d for d in validated_data if d.date >= cutoff_date]
        
        if len(recent_data) < 2:
            raise ValueError("Insufficient data for trend analysis")
            
        # Sort by date
        recent_data.sort(key=lambda x: x.date)
        
        # Group by month
        monthly_rates = defaultdict(list)
        for record in recent_data:
            month_key = record.date.strftime("%Y-%m")
            monthly_rates[month_key].append(record.rate)
            
        # Calculate monthly averages
        monthly_averages = {}
        for month, rates in monthly_rates.items():
            monthly_averages[month] = statistics.mean(rates)
            
        # Calculate trend using linear regression
        months = list(monthly_averages.keys())
        rates = list(monthly_averages.values())
        
        if len(months) < 2:
            raise ValueError("Need at least 2 months of data for trend analysis")
            
        # Simple linear regression
        x = list(range(len(months)))
        y = rates
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        # Calculate slope and intercept
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared
        y_mean = statistics.mean(y)
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction and strength
        if abs(slope) < 0.1:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
            
        # Normalize trend strength to -1 to 1
        max_rate_change = max(rates) - min(rates)
        trend_strength = min(1.0, max(0.0, abs(slope) / max_rate_change)) if max_rate_change > 0 else 0
        if slope < 0:
            trend_strength = -trend_strength
            
        # Calculate average change per month
        average_change_per_month = slope
        
        # Predict next month
        prediction_next_month = slope * len(x) + intercept
        
        # Analyze seasonal patterns (simplified)
        seasonal_patterns = {}
        for record in recent_data:
            quarter = f"Q{(record.date.month - 1) // 3 + 1}"
            if quarter not in seasonal_patterns:
                seasonal_patterns[quarter] = []
            seasonal_patterns[quarter].append(record.rate)
            
        for quarter in seasonal_patterns:
            seasonal_patterns[quarter] = statistics.mean(seasonal_patterns[quarter])
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=round(trend_strength, 4),
            average_change_per_month=round(average_change_per_month, 2),
            r_squared=round(r_squared, 4),
            confidence_level=round(r_squared * 100, 2),
            prediction_next_month=round(prediction_next_month, 2),
            seasonal_patterns=seasonal_patterns
        )
    
    def comparative_analysis(
        self, 
        data: Optional[List[RateData]] = None,
        top_n: int = 5
    ) -> ComparativeAnalysis:
        """Perform comparative analysis across different dimensions.
        
        Args:
            data: Optional rate data to analyze
            top_n: Number of top/bottom performers to include
            
        Returns:
            ComparativeAnalysis with comparison data
        """
        analysis_data = data if data is not None else self.rate_data
        
        if not analysis_data:
            raise ValueError("No rate data available for comparative analysis")
            
        validated_data = self._validate_rate_data(analysis_data)
        
        # Group by different dimensions
        by_project_type = defaultdict(list)
        by_skill_level = defaultdict(list)
        by_location = defaultdict(list)
        by_contractor = defaultdict(list)
        
        for record in validated_data:
            by_project_type[record.project_type].append(record.rate)
            by_skill_level[record.skill_level].append(record.rate)
            by_location[record.location].append(record.rate)
            by_contractor[record.contractor_id].append({
                'rate': record.rate,
                'date': record.date,
                'hours': record.hours_worked or 0
            })
        
        # Calculate statistics for each group
        def calculate_group_stats(groups):
            stats = {}
            for group_name, rates in groups.items():
                if rates:
                    stats[group_name] = {
                        'mean': round(statistics.mean(rates), 2),
                        'median': round(statistics.median(rates), 2),
                        'count': len(rates),
                        'std_dev': round(statistics.stdev(rates) if len(rates) > 1 else 0, 2),
                        'min': min(rates),
                        'max': max(rates)
                    }
            return stats
        
        # Time period analysis (last 6 months)
        by_time_period = {}
        current_date = datetime.now()
        for i in range(6):
            month_start = current_date.replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            month_name = month_start.strftime("%Y-%m")
            
            month_rates = [
                record.rate for record in validated_data
                if month_start <= record.date <= month_end
            ]
            
            if month_rates:
                by_time_period[month_name] = {
                    'mean': round(statistics.mean(month_rates), 2),
                    'count': len(month_rates),
                    'total_hours': sum(
                        record.hours_worked or 0 for record in validated_data
                        if month_start <= record.date <= month_end
                    )
                }
        
        # Find top and bottom performers
        contractor_stats = {}
        for contractor_id, records in by_contractor.items():
            rates = [r['rate'] for r in records]
            total_hours = sum(r['hours'] for r in records)
            
            if rates:
                contractor_stats[contractor_id] = {
                    'contractor_id': contractor_id,
                    'avg_rate': statistics.mean(rates),
                    'total_records': len(rates),
                    'total_hours': total_hours,
                    'revenue': sum(r['rate'] * r['hours'] for r in records if r['hours'] > 0),
                    'latest_date': max(r['date'] for r in records)
                }
        
        # Sort contractors by average rate
        sorted_contractors = sorted(
            contractor_stats.values(),
            key=lambda x: x['avg_rate'],
            reverse=True
        )
        
        top_performers = sorted_contractors[:top_n]
        bottom_performers = sorted_contractors[-top_n:] if len(sorted_contractors) > top_n else []
        
        # Round values for top/bottom performers
        for performer in top_performers + bottom_performers:
            performer['avg_rate'] = round(performer['avg_rate'], 2)
            performer['revenue'] = round(performer['revenue'], 2)
            performer['latest_date'] = performer['latest_date'].isoformat()
        
        return ComparativeAnalysis(
            by_project_type=calculate_group_stats(by_project_type),
            by_skill_level=calculate_group_stats(by_skill_level),
            by_location=calculate_group_stats(by_location),
            by_time_period=by_time_period,
            top_performers=top_performers,
            bottom_performers=bottom_performers
        )
    
    def get_rate_recommendations(
        self, 
        project_type: str,
        skill_level: str,
        location: str,
        data: Optional[List[RateData]] = None
    ) -> Dict[str, float]:
        """Get rate recommendations based on similar profiles.
        
        Args:
            project_type: Type of project
            skill_level: Skill level required
            location: Location of work
            data: Optional rate data to analyze
            
        Returns:
            Dictionary with rate recommendations
        """
        analysis_data = data if data is not None else self.rate_data
        
        if not analysis_data:
            raise ValueError("No rate data available for recommendations")
            
        validated_data = self._validate_rate_data(analysis_data)
        
        # Find similar profiles
        similar_rates = []
        exact_matches = []
        
        for record in validated_data:
            match_score = 0
            if record.project_type == project_type:
                match_score += 3
            if record.skill_level == skill_level:
                match_score += 3
            if record.location == location:
                match_score += 2
                
            if match_score >= 6:  # Exact match on project_type and skill_level
                exact_matches.append(record.rate)
            elif match_score >= 3:  # At least one major criterion matches
                similar_rates.append(record.rate)
        
        # Use exact matches if available, otherwise similar rates
        rates_to_use = exact_matches if exact_matches else similar_rates
        
        if not rates_to_use:
            # Fall back to all rates
            rates_to_use = [record.rate for record in validated_data]
        
        if not rates_to_use:
            raise ValueError("No suitable data for recommendations")
            
        # Calculate recommendations
        recommendations = {
            'conservative': round(np.percentile(rates_to_use, 25), 2),
            'market_rate': round(statistics.median(rates_to_use), 2),
            'competitive': round(np.percentile(rates_to_use, 75), 2),
            'premium': round(np.percentile(rates_to_use, 90), 2),
            'sample_size': len(rates_to_use),
            'exact_matches': len(exact_matches)
        }
        
        return recommendations


def analyze_rates(
    rate_data: List[Dict[str, Any]],
    analysis_type: str = 'basic',
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to analyze rates from dictionary data.
    
    Args:
        rate_data: List of dictionaries containing rate data
        analysis_type: Type of analysis ('basic', 'trend', 'comparative', 'recommendations')
        **kwargs: Additional arguments for specific analysis types
        
    Returns:
        Dictionary with analysis results
    """
    analyzer = RateAnalyzer()
    
    # Convert dictionary data to RateData objects
    rate_objects = []
    for item in rate_data:
        try:
            rate_obj = RateData(
                contractor_id=item.get('contractor_id', ''),
                rate=float(item.get('rate', 0)),
                currency=item.get('currency', 'USD'),
                date=datetime.fromisoformat(item.get('date', datetime.now().isoformat())),
                project_type=item.get('project_type', 'unknown'),
                skill_level=item.get('skill_level', 'unknown'),
                location=item.get('location', 'unknown'),
                hours_worked=item.get('hours_worked'),
                overtime_rate=item.get('overtime_rate')
            )
            rate_objects.append(rate_obj)
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid rate data: {e}")
            continue
    
    if not rate_objects:
        raise ValueError("No valid rate data provided")
        
    analyzer.add_rate_data(rate_objects)
    
    try:
        if analysis_type == 'basic':
            result = analyzer.analyze_rates(**kwargs)
            return result.to_dict()
        elif analysis_type == 'trend':
            result = analyzer.analyze_trends(**kwargs)
            return asdict(result)
        elif analysis_type == 'comparative':
            result = analyzer.comparative_analysis(**kwargs)
            return asdict(result)
        elif analysis_type == 'recommendations':
            required_fields = ['project_type', 'skill_level', 'location']
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(f"Missing required field for recommendations: {field}")
            return analyzer.get_rate_recommendations(**kwargs)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


def calculate_rate_statistics(rates: List[float]) -> Dict[str, float]:
    """Calculate basic statistics for a list of rates.
    
    Args:
        rates: List of numerical rates
        
    Returns:
        Dictionary with basic statistics
    """
    if not rates:
        return {}
        
    return {
        'count': len(rates),
        'mean': round(statistics.mean(rates), 2),
        'median': round(statistics.median(rates), 2),
        'mode': round(statistics.mode(rates), 2) if len(set(rates)) < len(rates) else None,
        'std_dev': round(statistics.stdev(rates) if len(rates) > 1 else 0, 2),
        'variance': round(statistics.variance(rates) if len(rates) > 1 else 0, 2),
        'min': min(rates),
        'max': max(rates),
        'range': round(max(rates) - min(rates), 2),
        'percentile_25': round(np.percentile(rates, 25), 2),
        'percentile_75': round(np.percentile(rates, 75), 2)
    }


def detect_rate_anomalies(
    rates: List[float], 
    method: str = 'zscore',
    threshold: float = 2.0
) -> List[int]:
    """Detect anomalies in rate data.
    
    Args:
        rates: List of rates to analyze
        method: Method to use ('zscore', 'iqr')
        threshold: Threshold for anomaly detection
        
    Returns:
        List of indices of anomalous rates
    """
    if len(rates) < 3:
        return []
        
    anomalies = []
    
    if method == 'zscore':
        mean_rate = statistics.mean(rates)
        std_dev = statistics.stdev(rates)
        
        if std_dev == 0:
            return []
            
        for i, rate in enumerate(rates):
            z_score = abs(rate - mean_rate) / std_dev
            if z_score > threshold:
                anomalies.append(i)
                
    elif method == 'iqr':
        q1 = np.percentile(rates, 25)
        q3 = np.percentile(rates, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        for i, rate in enumerate(rates):
            if rate < lower_bound or rate > upper_bound:
                anomalies.append(i)
    
    return anomalies