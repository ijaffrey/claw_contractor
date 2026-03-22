"""
Qualification Engine Module

This module provides functionality to calculate qualification scores for contractors
based on various criteria including experience, ratings, completion rate, and other factors.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class QualificationEngine:
    """
    Engine for calculating contractor qualification scores based on multiple criteria.
    """
    
    # Weight constants for different scoring criteria
    WEIGHTS = {
        'experience_years': 0.20,
        'completion_rate': 0.25,
        'average_rating': 0.20,
        'total_projects': 0.15,
        'recent_activity': 0.10,
        'certifications': 0.05,
        'response_time': 0.05
    }
    
    # Minimum thresholds
    MIN_PROJECTS_FOR_RELIABILITY = 3
    RECENT_ACTIVITY_DAYS = 90
    MAX_RESPONSE_TIME_HOURS = 24
    
    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize the qualification engine.
        
        Args:
            custom_weights: Optional custom weights for scoring criteria
        """
        if custom_weights:
            # Validate that weights sum to 1.0
            if abs(sum(custom_weights.values()) - 1.0) > 0.001:
                raise ValueError("Custom weights must sum to 1.0")
            self.weights = custom_weights
        else:
            self.weights = self.WEIGHTS.copy()
    
    def calculate_qualification_score(self, contractor_data: Dict[str, Any]) -> float:
        """
        Calculate the overall qualification score for a contractor.
        
        Args:
            contractor_data: Dictionary containing contractor information
            
        Returns:
            float: Qualification score between 0-100
            
        Expected contractor_data structure:
        {
            'experience_years': int,
            'completion_rate': float (0-1),
            'average_rating': float (0-5),
            'total_projects': int,
            'last_activity_date': datetime or str,
            'certifications': List[str],
            'average_response_time_hours': float,
            'project_history': List[Dict] (optional),
            'skills': List[str] (optional)
        }
        """
        try:
            # Validate input data
            self._validate_contractor_data(contractor_data)
            
            # Calculate individual component scores
            experience_score = self._calculate_experience_score(
                contractor_data.get('experience_years', 0)
            )
            
            completion_score = self._calculate_completion_score(
                contractor_data.get('completion_rate', 0.0),
                contractor_data.get('total_projects', 0)
            )
            
            rating_score = self._calculate_rating_score(
                contractor_data.get('average_rating', 0.0),
                contractor_data.get('total_projects', 0)
            )
            
            project_volume_score = self._calculate_project_volume_score(
                contractor_data.get('total_projects', 0)
            )
            
            activity_score = self._calculate_recent_activity_score(
                contractor_data.get('last_activity_date')
            )
            
            certification_score = self._calculate_certification_score(
                contractor_data.get('certifications', [])
            )
            
            response_time_score = self._calculate_response_time_score(
                contractor_data.get('average_response_time_hours', float('inf'))
            )
            
            # Calculate weighted total score
            total_score = (
                experience_score * self.weights['experience_years'] +
                completion_score * self.weights['completion_rate'] +
                rating_score * self.weights['average_rating'] +
                project_volume_score * self.weights['total_projects'] +
                activity_score * self.weights['recent_activity'] +
                certification_score * self.weights['certifications'] +
                response_time_score * self.weights['response_time']
            ) * 100
            
            # Ensure score is within bounds
            final_score = max(0.0, min(100.0, total_score))
            
            logger.debug(
                f"Qualification score calculated: {final_score:.2f} "
                f"(experience: {experience_score:.2f}, completion: {completion_score:.2f}, "
                f"rating: {rating_score:.2f}, projects: {project_volume_score:.2f}, "
                f"activity: {activity_score:.2f}, certs: {certification_score:.2f}, "
                f"response: {response_time_score:.2f})"
            )
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating qualification score: {str(e)}")
            raise
    
    def _validate_contractor_data(self, data: Dict[str, Any]) -> None:
        """Validate contractor data structure and types."""
        required_fields = ['experience_years', 'completion_rate', 'average_rating', 'total_projects']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing field '{field}' in contractor data, using default value")
        
        # Validate numeric ranges
        if 'completion_rate' in data and not 0 <= data['completion_rate'] <= 1:
            raise ValueError("completion_rate must be between 0 and 1")
        
        if 'average_rating' in data and not 0 <= data['average_rating'] <= 5:
            raise ValueError("average_rating must be between 0 and 5")
    
    def _calculate_experience_score(self, experience_years: int) -> float:
        """
        Calculate score based on years of experience.
        Score increases logarithmically with experience.
        """
        if experience_years <= 0:
            return 0.0
        
        # Logarithmic scoring favoring experienced contractors
        # 1 year = ~0.3, 5 years = ~0.7, 10+ years = ~1.0
        score = min(1.0, math.log(experience_years + 1) / math.log(11))
        return score
    
    def _calculate_completion_score(self, completion_rate: float, total_projects: int) -> float:
        """
        Calculate score based on project completion rate.
        Applies reliability penalty for contractors with few projects.
        """
        if total_projects == 0:
            return 0.0
        
        base_score = completion_rate
        
        # Apply reliability penalty for contractors with few completed projects
        if total_projects < self.MIN_PROJECTS_FOR_RELIABILITY:
            reliability_factor = total_projects / self.MIN_PROJECTS_FOR_RELIABILITY
            base_score *= reliability_factor
        
        return base_score
    
    def _calculate_rating_score(self, average_rating: float, total_projects: int) -> float:
        """
        Calculate score based on average client rating.
        Normalizes 5-star rating to 0-1 scale.
        """
        if total_projects == 0 or average_rating <= 0:
            return 0.0
        
        # Normalize 5-star rating to 0-1 scale
        base_score = average_rating / 5.0
        
        # Apply reliability penalty for contractors with few ratings
        if total_projects < self.MIN_PROJECTS_FOR_RELIABILITY:
            reliability_factor = total_projects / self.MIN_PROJECTS_FOR_RELIABILITY
            base_score *= reliability_factor
        
        return base_score
    
    def _calculate_project_volume_score(self, total_projects: int) -> float:
        """
        Calculate score based on total number of completed projects.
        Uses logarithmic scaling to prevent extremely high scores for very active contractors.
        """
        if total_projects <= 0:
            return 0.0
        
        # Logarithmic scoring: 1 project = ~0.1, 10 projects = ~0.5, 100+ projects = ~1.0
        score = min(1.0, math.log(total_projects + 1) / math.log(101))
        return score
    
    def _calculate_recent_activity_score(self, last_activity_date: Any) -> float:
        """
        Calculate score based on recent activity.
        Higher scores for more recent activity.
        """
        if not last_activity_date:
            return 0.0
        
        # Convert string to datetime if necessary
        if isinstance(last_activity_date, str):
            try:
                last_activity_date = datetime.fromisoformat(last_activity_date.replace('Z', '+00:00'))
            except ValueError:
                logger.warning("Invalid date format for last_activity_date")
                return 0.0
        
        if not isinstance(last_activity_date, datetime):
            logger.warning("last_activity_date must be datetime or ISO string")
            return 0.0
        
        days_since_activity = (datetime.now(last_activity_date.tzinfo) - last_activity_date).days
        
        if days_since_activity < 0:
            days_since_activity = 0
        
        # Linear decay over RECENT_ACTIVITY_DAYS
        if days_since_activity <= self.RECENT_ACTIVITY_DAYS:
            score = 1.0 - (days_since_activity / self.RECENT_ACTIVITY_DAYS)
        else:
            score = 0.0
        
        return max(0.0, score)
    
    def _calculate_certification_score(self, certifications: List[str]) -> float:
        """
        Calculate score based on professional certifications.
        More certifications result in higher scores with diminishing returns.
        """
        if not certifications:
            return 0.0
        
        num_certifications = len(certifications)
        
        # Square root scaling for diminishing returns
        # 1 cert = 0.32, 4 certs = 0.63, 9 certs = 0.95, 16+ certs = 1.0
        score = min(1.0, math.sqrt(num_certifications) / 4.0)
        return score
    
    def _calculate_response_time_score(self, avg_response_time_hours: float) -> float:
        """
        Calculate score based on average response time.
        Faster response times receive higher scores.
        """
        if avg_response_time_hours == float('inf') or avg_response_time_hours < 0:
            return 0.0
        
        # Linear decay from 1.0 at 0 hours to 0.0 at MAX_RESPONSE_TIME_HOURS
        if avg_response_time_hours <= self.MAX_RESPONSE_TIME_HOURS:
            score = 1.0 - (avg_response_time_hours / self.MAX_RESPONSE_TIME_HOURS)
        else:
            score = 0.0
        
        return max(0.0, score)
    
    def get_score_breakdown(self, contractor_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get detailed breakdown of qualification score components.
        
        Args:
            contractor_data: Dictionary containing contractor information
            
        Returns:
            Dict with component scores and weights
        """
        try:
            self._validate_contractor_data(contractor_data)
            
            components = {
                'experience_years': self._calculate_experience_score(
                    contractor_data.get('experience_years', 0)
                ),
                'completion_rate': self._calculate_completion_score(
                    contractor_data.get('completion_rate', 0.0),
                    contractor_data.get('total_projects', 0)
                ),
                'average_rating': self._calculate_rating_score(
                    contractor_data.get('average_rating', 0.0),
                    contractor_data.get('total_projects', 0)
                ),
                'total_projects': self._calculate_project_volume_score(
                    contractor_data.get('total_projects', 0)
                ),
                'recent_activity': self._calculate_recent_activity_score(
                    contractor_data.get('last_activity_date')
                ),
                'certifications': self._calculate_certification_score(
                    contractor_data.get('certifications', [])
                ),
                'response_time': self._calculate_response_time_score(
                    contractor_data.get('average_response_time_hours', float('inf'))
                )
            }
            
            # Add weighted scores and total
            breakdown = {}
            total_weighted_score = 0.0
            
            for component, score in components.items():
                weight = self.weights[component]
                weighted_score = score * weight * 100
                total_weighted_score += weighted_score
                
                breakdown[component] = {
                    'raw_score': round(score, 3),
                    'weight': weight,
                    'weighted_score': round(weighted_score, 2)
                }
            
            breakdown['total_score'] = round(total_weighted_score, 2)
            breakdown['weights'] = self.weights.copy()
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error generating score breakdown: {str(e)}")
            raise


# Convenience function for backward compatibility and simple usage
def calculate_qualification_score(contractor_data: Dict[str, Any]) -> float:
    """
    Calculate qualification score using default weights.
    
    Args:
        contractor_data: Dictionary containing contractor information
        
    Returns:
        float: Qualification score between 0-100
    """
    engine = QualificationEngine()
    return engine.calculate_qualification_score(contractor_data)


def get_qualification_breakdown(contractor_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Get detailed qualification score breakdown using default weights.
    
    Args:
        contractor_data: Dictionary containing contractor information
        
    Returns:
        Dict with detailed score breakdown
    """
    engine = QualificationEngine()
    return engine.get_score_breakdown(contractor_data)