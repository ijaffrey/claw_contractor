#!/usr/bin/env python3
"""
AI Developer Screening System - Main Entry Point

This module provides the main interface for the AI developer screening system,
including candidate assessment, interview scheduling, and result analysis.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_modules():
    """Import all required modules with proper error handling."""
    modules = {}
    
    try:
        from candidate_assessment import CandidateAssessment
        modules['candidate_assessment'] = CandidateAssessment
        logger.info("Successfully imported candidate_assessment module")
    except ImportError as e:
        logger.error(f"Failed to import candidate_assessment: {e}")
        modules['candidate_assessment'] = None
    
    try:
        from interview_scheduler import InterviewScheduler
        modules['interview_scheduler'] = InterviewScheduler
        logger.info("Successfully imported interview_scheduler module")
    except ImportError as e:
        logger.error(f"Failed to import interview_scheduler: {e}")
        modules['interview_scheduler'] = None
    
    try:
        from ai_evaluator import AIEvaluator
        modules['ai_evaluator'] = AIEvaluator
        logger.info("Successfully imported ai_evaluator module")
    except ImportError as e:
        logger.error(f"Failed to import ai_evaluator: {e}")
        modules['ai_evaluator'] = None
    
    try:
        from code_reviewer import CodeReviewer
        modules['code_reviewer'] = CodeReviewer
        logger.info("Successfully imported code_reviewer module")
    except ImportError as e:
        logger.error(f"Failed to import code_reviewer: {e}")
        modules['code_reviewer'] = None
    
    try:
        from skill_analyzer import SkillAnalyzer
        modules['skill_analyzer'] = SkillAnalyzer
        logger.info("Successfully imported skill_analyzer module")
    except ImportError as e:
        logger.error(f"Failed to import skill_analyzer: {e}")
        modules['skill_analyzer'] = None
    
    return modules

def dry_run_qualification_check(candidate_data: Dict[str, Any]) -> None:
    """
    Perform a dry run qualification score check without actual processing.
    
    Args:
        candidate_data: Dictionary containing candidate information
    """
    print("\n" + "="*60)
    print("DRY RUN - QUALIFICATION SCORE CHECK")
    print("="*60)
    
    # Basic qualification scoring logic
    score = 0
    max_score = 100
    
    # Experience scoring (30 points max)
    experience_years = candidate_data.get('experience_years', 0)
    if experience_years >= 5:
        experience_score = 30
    elif experience_years >= 3:
        experience_score = 20
    elif experience_years >= 1:
        experience_score = 15
    else:
        experience_score = 5
    score += experience_score
    
    # Skills scoring (40 points max)
    required_skills = ['python', 'ai', 'machine learning', 'data science']
    candidate_skills = [skill.lower() for skill in candidate_data.get('skills', [])]
    skill_matches = sum(1 for skill in required_skills if skill in ' '.join(candidate_skills))
    skill_score = min(skill_matches * 10, 40)
    score += skill_score
    
    # Education scoring (20 points max)
    education = candidate_data.get('education', '').lower()
    if 'phd' in education or 'doctorate' in education:
        education_score = 20
    elif 'master' in education or 'ms' in education or 'msc' in education:
        education_score = 15
    elif 'bachelor' in education or 'bs' in education or 'bsc' in education:
        education_score = 10
    else:
        education_score = 5
    score += education_score
    
    # Portfolio scoring (10 points max)
    portfolio_items = candidate_data.get('portfolio_items', 0)
    portfolio_score = min(portfolio_items * 2, 10)
    score += portfolio_score
    
    # Display results
    print(f"Candidate: {candidate_data.get('name', 'Unknown')}")
    print(f"Email: {candidate_data.get('email', 'Not provided')}")
    print("\nScoring Breakdown:")
    print(f"  Experience ({experience_years} years): {experience_score}/30")
    print(f"  Skills (matched {skill_matches}/{len(required_skills)}): {skill_score}/40")
    print(f"  Education: {education_score}/20")
    print(f"  Portfolio ({portfolio_items} items): {portfolio_score}/10")
    print(f"\nTotal Score: {score}/{max_score} ({score/max_score*100:.1f}%)")
    
    # Qualification determination
    if score >= 70:
        qualification = "HIGHLY QUALIFIED"
        recommendation = "Proceed to technical interview"
    elif score >= 50:
        qualification = "QUALIFIED"
        recommendation = "Proceed with standard assessment"
    elif score >= 30:
        qualification = "POTENTIALLY QUALIFIED"
        recommendation = "Consider for junior positions or additional screening"
    else:
        qualification = "NOT QUALIFIED"
        recommendation = "Does not meet minimum requirements"
    
    print(f"\nQualification Status: {qualification}")
    print(f"Recommendation: {recommendation}")
    print("="*60)

def run_assessment(modules: Dict[str, Any], candidate_data: Dict[str, Any], dry_run: bool = False) -> None:
    """
    Run the complete candidate assessment process.
    
    Args:
        modules: Dictionary of imported modules
        candidate_data: Dictionary containing candidate information
        dry_run: Whether to run in dry-run mode
    """
    if dry_run:
        dry_run_qualification_check(candidate_data)
        return
    
    print(f"Starting assessment for candidate: {candidate_data.get('name', 'Unknown')}")
    
    # Initialize components
    results = {}
    
    # Candidate Assessment
    if modules['candidate_assessment']:
        try:
            assessor = modules['candidate_assessment']()
            assessment_result = assessor.evaluate_candidate(candidate_data)
            results['assessment'] = assessment_result
            logger.info("Candidate assessment completed successfully")
        except Exception as e:
            logger.error(f"Error during candidate assessment: {e}")
            results['assessment'] = None
    
    # AI Evaluation
    if modules['ai_evaluator']:
        try:
            evaluator = modules['ai_evaluator']()
            ai_result = evaluator.evaluate_technical_skills(candidate_data)
            results['ai_evaluation'] = ai_result
            logger.info("AI evaluation completed successfully")
        except Exception as e:
            logger.error(f"Error during AI evaluation: {e}")
            results['ai_evaluation'] = None
    
    # Code Review
    if modules['code_reviewer'] and candidate_data.get('code_samples'):
        try:
            reviewer = modules['code_reviewer']()
            review_result = reviewer.review_code(candidate_data['code_samples'])
            results['code_review'] = review_result
            logger.info("Code review completed successfully")
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            results['code_review'] = None
    
    # Skill Analysis
    if modules['skill_analyzer']:
        try:
            analyzer = modules['skill_analyzer']()
            skill_result = analyzer.analyze_skills(candidate_data)
            results['skill_analysis'] = skill_result
            logger.info("Skill analysis completed successfully")
        except Exception as e:
            logger.error(f"Error during skill analysis: {e}")
            results['skill_analysis'] = None
    
    # Schedule interview if qualified
    if modules['interview_scheduler'] and results.get('assessment', {}).get('qualified', False):
        try:
            scheduler = modules['interview_scheduler']()
            interview_result = scheduler.schedule_interview(candidate_data, results)
            results['interview'] = interview_result
            logger.info("Interview scheduled successfully")
        except Exception as e:
            logger.error(f"Error scheduling interview: {e}")
            results['interview'] = None
    
    # Display results
    print("\nAssessment Results:")
    print("="*50)
    for component, result in results.items():
        if result:
            print(f"{component.title()}: ✓ Completed")
        else:
            print(f"{component.title()}: ✗ Failed or Skipped")
    print("="*50)

def main():
    """Main entry point for the AI developer screening system."""
    parser = argparse.ArgumentParser(
        description="AI Developer Screening System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --candidate-file candidate.json
  python main.py --dry-run --candidate-file candidate.json
  python main.py --name "John Doe" --email "john@example.com" --dry-run
        """
    )
    
    parser.add_argument(
        '--candidate-file',
        type=str,
        help='Path to JSON file containing candidate data'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        help='Candidate name (for quick testing)'
    )
    
    parser.add_argument(
        '--email',
        type=str,
        help='Candidate email (for quick testing)'
    )
    
    parser.add_argument(
        '--skills',
        nargs='+',
        help='List of candidate skills (for quick testing)'
    )
    
    parser.add_argument(
        '--experience-years',
        type=int,
        default=0,
        help='Years of experience (for quick testing)'
    )
    
    parser.add_argument(
        '--education',
        type=str,
        help='Education level (for quick testing)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run qualification score check without full assessment'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Import modules
    print("Initializing AI Developer Screening System...")
    modules = import_modules()
    
    # Check if any modules failed to import
    failed_imports = [name for name, module in modules.items() if module is None]
    if failed_imports and not args.dry_run:
        logger.warning(f"Some modules failed to import: {failed_imports}")
        logger.warning("System will run with limited functionality")
    
    # Prepare candidate data
    candidate_data = {}
    
    if args.candidate_file:
        try:
            import json
            candidate_file = Path(args.candidate_file)
            if candidate_file.exists():
                with open(candidate_file, 'r') as f:
                    candidate_data = json.load(f)
                logger.info(f"Loaded candidate data from {args.candidate_file}")
            else:
                logger.error(f"Candidate file not found: {args.candidate_file}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading candidate file: {e}")
            sys.exit(1)
    else:
        # Use command line arguments
        candidate_data = {
            'name': args.name or 'Test Candidate',
            'email': args.email or 'test@example.com',
            'skills': args.skills or ['Python', 'AI', 'Machine Learning'],
            'experience_years': args.experience_years,
            'education': args.education or 'Bachelor\'s Degree',
            'portfolio_items': 3  # Default for testing
        }
    
    if not candidate_data:
        logger.error("No candidate data provided")
        parser.print_help()
        sys.exit(1)
    
    try:
        # Run assessment
        run_assessment(modules, candidate_data, args.dry_run)
        
        if not args.dry_run:
            print("\nAssessment process completed successfully!")
        else:
            print("\nDry run completed!")
            
    except KeyboardInterrupt:
        logger.info("Assessment interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error during assessment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()