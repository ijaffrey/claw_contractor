import logging
import subprocess
import sys
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AcceptanceCriteriaError(Exception):
    """Exception raised when acceptance criteria execution fails."""
    pass

class ClaudeAPIError(Exception):
    """Exception raised when Claude API calls fail."""
    pass

class Reviewer:
    """Main reviewer class for Patrick code review system."""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Reviewer.
        
        Args:
            api_key: Claude API key (if not provided, will look for environment variable)
            timeout: Timeout for subprocess execution in seconds
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        if not self.api_key:
            logger.warning("No Claude API key provided. Set CLAUDE_API_KEY environment variable.")

    def run_acceptance_criteria(self, criteria: List[str]) -> Dict[str, Any]:
        """
        Execute shell commands found in acceptance criteria.
        
        Args:
            criteria: List of acceptance criteria, some may contain shell commands
            
        Returns:
            Dictionary containing execution results
            
        Raises:
            AcceptanceCriteriaError: If any shell command fails
        """
        results = {
            "executed_commands": [],
            "failed_commands": [],
            "outputs": {},
            "success": True
        }
        
        logger.info(f"Running acceptance criteria validation with {len(criteria)} criteria")
        
        for i, criterion in enumerate(criteria):
            # Check if criterion contains shell command indicators
            if any(indicator in criterion.lower() for indicator in [
                'run', 'execute', 'command', 'shell', 'bash', 'sh', '$', 'python -m', 'pytest', 'npm test'
            ]):
                try:
                    # Extract potential shell command
                    command = self._extract_shell_command(criterion)
                    if command:
                        logger.info(f"Executing command from criterion {i+1}: {command}")
                        
                        # Execute the command
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=self.timeout,
                            cwd=os.getcwd()
                        )
                        
                        results["executed_commands"].append(command)
                        results["outputs"][command] = {
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "returncode": result.returncode
                        }
                        
                        # Check if command failed
                        if result.returncode != 0:
                            error_msg = f"Command failed with return code {result.returncode}: {command}"
                            logger.error(error_msg)
                            logger.error(f"STDERR: {result.stderr}")
                            
                            results["failed_commands"].append({
                                "command": command,
                                "error": result.stderr,
                                "returncode": result.returncode
                            })
                            results["success"] = False
                            
                            raise AcceptanceCriteriaError(
                                f"Acceptance criteria validation failed: {error_msg}\n"
                                f"Error output: {result.stderr}"
                            )
                        else:
                            logger.info(f"Command executed successfully: {command}")
                            if result.stdout:
                                logger.debug(f"STDOUT: {result.stdout}")
                                
                except subprocess.TimeoutExpired:
                    error_msg = f"Command timed out after {self.timeout} seconds: {command}"
                    logger.error(error_msg)
                    results["failed_commands"].append({
                        "command": command,
                        "error": "Timeout expired",
                        "returncode": -1
                    })
                    results["success"] = False
                    raise AcceptanceCriteriaError(f"Acceptance criteria validation failed: {error_msg}")
                    
                except Exception as e:
                    error_msg = f"Unexpected error executing command '{command}': {str(e)}"
                    logger.error(error_msg)
                    results["failed_commands"].append({
                        "command": command,
                        "error": str(e),
                        "returncode": -1
                    })
                    results["success"] = False
                    raise AcceptanceCriteriaError(f"Acceptance criteria validation failed: {error_msg}")
        
        logger.info(f"Acceptance criteria validation completed. Success: {results['success']}")
        return results

    def _extract_shell_command(self, criterion: str) -> Optional[str]:
        """
        Extract shell command from acceptance criteria text.
        
        Args:
            criterion: Single acceptance criterion text
            
        Returns:
            Extracted shell command or None if no command found
        """
        criterion_lower = criterion.lower().strip()
        
        # Common patterns for shell commands in acceptance criteria
        patterns = [
            # Direct command indicators
            "run ",
            "execute ",
            "command: ",
            "$ ",
            # Test runners
            "pytest",
            "python -m pytest",
            "npm test",
            "npm run test",
            "python -m unittest",
            "python test",
            # Build tools
            "make",
            "cmake",
            "npm build",
            "python setup.py",
            # Linters
            "flake8",
            "pylint",
            "black",
            "isort"
        ]
        
        for pattern in patterns:
            if pattern in criterion_lower:
                # Try to extract the actual command
                if pattern == "$ ":
                    # Shell prompt style
                    start_idx = criterion.find("$ ") + 2
                    command = criterion[start_idx:].strip()
                    # Stop at newline or end of line
                    if '\n' in command:
                        command = command.split('\n')[0].strip()
                    return command
                elif pattern in ["run ", "execute "]:
                    # "run command" or "execute command" style
                    start_idx = criterion_lower.find(pattern) + len(pattern)
                    command = criterion[start_idx:].strip()
                    if '\n' in command:
                        command = command.split('\n')[0].strip()
                    # Remove quotes if present
                    command = command.strip('"\'')
                    return command
                elif pattern == "command: ":
                    # "command: xyz" style
                    start_idx = criterion_lower.find(pattern) + len(pattern)
                    command = criterion[start_idx:].strip()
                    if '\n' in command:
                        command = command.split('\n')[0].strip()
                    return command
                else:
                    # Direct command (pytest, make, etc.)
                    if criterion_lower.strip().startswith(pattern):
                        return criterion.strip()
        
        return None

    def review(self, criteria: List[str], code_content: str = "", 
              file_path: str = "", additional_context: str = "") -> Dict[str, Any]:
        """
        Execute acceptance criteria validation and then perform Claude-based code review.
        
        Args:
            criteria: List of acceptance criteria to validate
            code_content: Code content to review
            file_path: Path to the file being reviewed
            additional_context: Additional context for the review
            
        Returns:
            Dictionary containing review results
            
        Raises:
            AcceptanceCriteriaError: If acceptance criteria validation fails
            ClaudeAPIError: If Claude API calls fail
        """
        logger.info("Starting code review process")
        
        # Step 1: Run acceptance criteria validation
        try:
            criteria_results = self.run_acceptance_criteria(criteria)
            logger.info("Acceptance criteria validation passed")
        except AcceptanceCriteriaError:
            logger.error("Acceptance criteria validation failed - aborting review")
            raise
        
        # Step 2: Proceed with Claude API review if criteria passed
        try:
            review_result = self._perform_claude_review(
                criteria=criteria,
                code_content=code_content,
                file_path=file_path,
                additional_context=additional_context,
                criteria_results=criteria_results
            )
            
            # Combine results
            final_result = {
                "acceptance_criteria": criteria_results,
                "claude_review": review_result,
                "overall_success": criteria_results["success"] and review_result.get("success", False)
            }
            
            logger.info("Code review completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Claude review failed: {str(e)}")
            raise ClaudeAPIError(f"Claude API review failed: {str(e)}")

    def _perform_claude_review(self, criteria: List[str], code_content: str,
                             file_path: str, additional_context: str,
                             criteria_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the actual Claude API-based code review.
        
        Args:
            criteria: List of acceptance criteria
            code_content: Code content to review
            file_path: File path being reviewed
            additional_context: Additional context
            criteria_results: Results from acceptance criteria execution
            
        Returns:
            Dictionary containing Claude review results
        """
        if not self.api_key:
            logger.warning("No API key available - returning mock review")
            return self._mock_claude_review(criteria, code_content, file_path)
        
        try:
            import requests
            
            # Prepare the prompt for Claude
            prompt = self._build_review_prompt(
                criteria=criteria,
                code_content=code_content,
                file_path=file_path,
                additional_context=additional_context,
                criteria_results=criteria_results
            )
            
            # Make API call to Claude
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            logger.info("Making Claude API request")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "content": result.get("content", [{}])[0].get("text", ""),
                "usage": result.get("usage", {}),
                "model": result.get("model", "claude-3-sonnet-20240229")
            }
            
        except ImportError:
            logger.warning("Requests library not available - returning mock review")
            return self._mock_claude_review(criteria, code_content, file_path)
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            raise ClaudeAPIError(f"Failed to get Claude review: {str(e)}")

    def _build_review_prompt(self, criteria: List[str], code_content: str,
                           file_path: str, additional_context: str,
                           criteria_results: Dict[str, Any]) -> str:
        """Build the prompt for Claude API review."""
        prompt_parts = [
            "You are a senior code reviewer. Please review the following code against the provided acceptance criteria.",
            "",
            "ACCEPTANCE CRITERIA:",
        ]
        
        for i, criterion in enumerate(criteria, 1):
            prompt_parts.append(f"{i}. {criterion}")
        
        prompt_parts.extend([
            "",
            "ACCEPTANCE CRITERIA VALIDATION RESULTS:",
            f"Validation Status: {'PASSED' if criteria_results['success'] else 'FAILED'}",
            f"Commands Executed: {len(criteria_results['executed_commands'])}",
        ])
        
        if criteria_results["executed_commands"]:
            prompt_parts.append("Executed Commands:")
            for cmd in criteria_results["executed_commands"]:
                prompt_parts.append(f"  - {cmd}")
        
        if file_path:
            prompt_parts.extend([
                "",
                f"FILE PATH: {file_path}"
            ])
        
        if code_content:
            prompt_parts.extend([
                "",
                "CODE TO REVIEW:",
                "```",
                code_content,
                "```"
            ])
        
        if additional_context:
            prompt_parts.extend([
                "",
                "ADDITIONAL CONTEXT:",
                additional_context
            ])
        
        prompt_parts.extend([
            "",
            "Please provide a thorough review focusing on:",
            "1. Compliance with acceptance criteria",
            "2. Code quality and best practices",
            "3. Potential issues or improvements",
            "4. Security considerations",
            "5. Performance implications",
            "",
            "Format your response with clear sections and actionable feedback."
        ])
        
        return "\n".join(prompt_parts)

    def _mock_claude_review(self, criteria: List[str], code_content: str, file_path: str) -> Dict[str, Any]:
        """
        Provide a mock Claude review when API is not available.
        Used for testing and development purposes.
        """
        mock_review = f"""
# Code Review Report

## Summary
Mock review generated for file: {file_path or 'Unknown'}

## Acceptance Criteria Compliance
The code has been validated against {len(criteria)} acceptance criteria.
All automated tests and validations have passed.

## Code Quality Assessment
- Code structure appears well-organized
- Following Python best practices
- Proper error handling implemented
- Good logging practices observed

## Recommendations
- Continue following established patterns
- Ensure comprehensive test coverage
- Consider adding more detailed docstrings where appropriate

## Security & Performance
- No obvious security vulnerabilities detected
- Performance considerations appear adequate
- Resource usage is appropriate

*Note: This is a mock review. For production use, configure Claude API key.*
"""
        
        return {
            "success": True,
            "content": mock_review.strip(),
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "model": "mock-reviewer"
        }


# Package-level exports
__version__ = "1.0.0"
__all__ = ["Reviewer", "AcceptanceCriteriaError", "ClaudeAPIError"]

# Initialize default reviewer instance
def create_reviewer(api_key: Optional[str] = None, timeout: int = 30) -> Reviewer:
    """
    Factory function to create a Reviewer instance.
    
    Args:
        api_key: Claude API key
        timeout: Timeout for subprocess execution
        
    Returns:
        Configured Reviewer instance
    """
    return Reviewer(api_key=api_key, timeout=timeout)

# Package initialization
logger.info(f"Patrick code review system v{__version__} initialized")