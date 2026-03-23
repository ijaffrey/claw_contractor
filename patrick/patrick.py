import os
from typing import Optional, List, Dict, Any
from .slack_bot import SlackBot


class Patrick:
    """Main Patrick module for integrating with Slack and providing feedback on step completions and failures."""
    
    def __init__(self, slack_bot: Optional[SlackBot] = None):
        """Initialize Patrick with optional SlackBot instance.
        
        Args:
            slack_bot: Optional SlackBot instance. If None, will attempt to create one from environment variables.
        """
        self.slack_bot = slack_bot
        self.channel = "#patrick"
        
        if self.slack_bot is None:
            self._initialize_slack_bot()
    
    def _initialize_slack_bot(self) -> None:
        """Initialize SlackBot from environment variables if tokens are available."""
        slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        slack_app_token = os.getenv('SLACK_APP_TOKEN')
        
        if slack_bot_token and slack_app_token:
            try:
                self.slack_bot = SlackBot(
                    bot_token=slack_bot_token,
                    app_token=slack_app_token
                )
            except Exception as e:
                print(f"Warning: Failed to initialize SlackBot: {e}")
                self.slack_bot = None
        else:
            print("Warning: SLACK_BOT_TOKEN and/or SLACK_APP_TOKEN not found in environment variables")
    
    def post_completion(self, message: str) -> bool:
        """Post a step completion message to Slack or print to terminal.
        
        Args:
            message: The completion message to post
            
        Returns:
            bool: True if message was posted successfully, False otherwise
        """
        if self.slack_bot:
            try:
                response = self.slack_bot.post_message(self.channel, f"✅ {message}")
                return response.get('ok', False)
            except Exception as e:
                print(f"Error posting to Slack: {e}")
                print(f"✅ {message}")
                return False
        else:
            print(f"✅ {message}")
            return True
    
    def post_failure(self, violations: List[Dict[str, Any]]) -> bool:
        """Post step failure violations to Slack or print to terminal.
        
        Args:
            violations: List of violation dictionaries containing details about failures
            
        Returns:
            bool: True if message was posted successfully, False otherwise
        """
        if not violations:
            return True
            
        failure_message = self._format_failure_message(violations)
        
        if self.slack_bot:
            try:
                response = self.slack_bot.post_message(self.channel, failure_message)
                return response.get('ok', False)
            except Exception as e:
                print(f"Error posting to Slack: {e}")
                print(failure_message)
                return False
        else:
            print(failure_message)
            return True
    
    def _format_failure_message(self, violations: List[Dict[str, Any]]) -> str:
        """Format violations into a readable failure message.
        
        Args:
            violations: List of violation dictionaries
            
        Returns:
            str: Formatted failure message
        """
        message_parts = ["❌ Step Failed - Violations Detected:"]
        
        for i, violation in enumerate(violations, 1):
            violation_text = f"\n{i}. "
            
            if 'type' in violation:
                violation_text += f"**{violation['type']}**: "
            
            if 'description' in violation:
                violation_text += violation['description']
            elif 'message' in violation:
                violation_text += violation['message']
            else:
                violation_text += str(violation)
            
            if 'file' in violation:
                violation_text += f" (File: {violation['file']}"
                if 'line' in violation:
                    violation_text += f", Line: {violation['line']}"
                violation_text += ")"
            
            message_parts.append(violation_text)
        
        return "".join(message_parts)
    
    def post_message(self, message: str, channel: Optional[str] = None) -> bool:
        """Post a generic message to Slack or print to terminal.
        
        Args:
            message: The message to post
            channel: Optional channel override (defaults to #patrick)
            
        Returns:
            bool: True if message was posted successfully, False otherwise
        """
        target_channel = channel or self.channel
        
        if self.slack_bot:
            try:
                response = self.slack_bot.post_message(target_channel, message)
                return response.get('ok', False)
            except Exception as e:
                print(f"Error posting to Slack: {e}")
                print(message)
                return False
        else:
            print(message)
            return True
    
    def is_slack_enabled(self) -> bool:
        """Check if Slack integration is enabled and available.
        
        Returns:
            bool: True if SlackBot is available, False otherwise
        """
        return self.slack_bot is not None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Patrick instance.
        
        Returns:
            dict: Health check results including Slack connectivity status
        """
        health_status = {
            'slack_enabled': self.is_slack_enabled(),
            'status': 'healthy'
        }
        
        if self.slack_bot:
            try:
                # Test Slack connection
                test_response = self.slack_bot.client.auth_test()
                health_status['slack_connection'] = test_response.get('ok', False)
                health_status['bot_user_id'] = test_response.get('user_id')
            except Exception as e:
                health_status['slack_connection'] = False
                health_status['slack_error'] = str(e)
                health_status['status'] = 'degraded'
        else:
            health_status['slack_connection'] = False
        
        return health_status


# Module-level initialization
def create_patrick() -> Patrick:
    """Factory function to create a Patrick instance with automatic configuration.
    
    Returns:
        Patrick: Configured Patrick instance
    """
    return Patrick()


# Default instance for convenient importing
patrick = create_patrick()