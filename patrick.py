import os
import sys
from typing import Optional
from slack_bot import SlackBot


class Patrick:
    def __init__(self):
        self.slack_bot = self._initialize_slack_bot()
        self.channel = "#patrick"
        
    def _initialize_slack_bot(self) -> Optional[SlackBot]:
        """Initialize SlackBot if tokens are available in environment."""
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        user_token = os.getenv("SLACK_USER_TOKEN")
        
        if bot_token and user_token:
            try:
                return SlackBot(bot_token, user_token)
            except Exception as e:
                print(f"Failed to initialize SlackBot: {e}", file=sys.stderr)
                return None
        return None
    
    def post_step_completion(self, step_name: str, details: Optional[str] = None):
        """Post successful step completion to Slack or terminal."""
        message = f"✅ Step completed: {step_name}"
        if details:
            message += f"\n{details}"
            
        if self.slack_bot:
            try:
                self.slack_bot.post_message(self.channel, message)
            except Exception as e:
                print(f"Failed to post to Slack: {e}", file=sys.stderr)
                self._fallback_to_terminal(message)
        else:
            self._fallback_to_terminal(message)
    
    def post_step_failure(self, step_name: str, violations: list, error_details: Optional[str] = None):
        """Post step failure with violations to Slack or terminal."""
        message = f"❌ Step failed: {step_name}"
        
        if violations:
            message += "\n\n**Violations:**"
            for i, violation in enumerate(violations, 1):
                message += f"\n{i}. {violation}"
        
        if error_details:
            message += f"\n\n**Error Details:**\n{error_details}"
            
        if self.slack_bot:
            try:
                self.slack_bot.post_message(self.channel, message)
            except Exception as e:
                print(f"Failed to post to Slack: {e}", file=sys.stderr)
                self._fallback_to_terminal(message)
        else:
            self._fallback_to_terminal(message)
    
    def post_general_message(self, message: str):
        """Post a general message to Slack or terminal."""
        if self.slack_bot:
            try:
                self.slack_bot.post_message(self.channel, message)
            except Exception as e:
                print(f"Failed to post to Slack: {e}", file=sys.stderr)
                self._fallback_to_terminal(message)
        else:
            self._fallback_to_terminal(message)
    
    def _fallback_to_terminal(self, message: str):
        """Fallback to terminal output when Slack is not available."""
        print(f"[PATRICK] {message}")
    
    def is_slack_enabled(self) -> bool:
        """Check if Slack integration is enabled and working."""
        return self.slack_bot is not None


# Global instance
_patrick_instance = None


def get_patrick() -> Patrick:
    """Get or create the global Patrick instance."""
    global _patrick_instance
    if _patrick_instance is None:
        _patrick_instance = Patrick()
    return _patrick_instance


def post_step_completion(step_name: str, details: Optional[str] = None):
    """Convenience function to post step completion."""
    patrick = get_patrick()
    patrick.post_step_completion(step_name, details)


def post_step_failure(step_name: str, violations: list, error_details: Optional[str] = None):
    """Convenience function to post step failure."""
    patrick = get_patrick()
    patrick.post_step_failure(step_name, violations, error_details)


def post_message(message: str):
    """Convenience function to post general message."""
    patrick = get_patrick()
    patrick.post_general_message(message)


def main():
    """Main function for testing Patrick functionality."""
    patrick = get_patrick()
    
    if patrick.is_slack_enabled():
        print("Patrick initialized with Slack integration enabled")
    else:
        print("Patrick initialized with terminal fallback (Slack tokens not available)")
    
    # Test messages
    patrick.post_general_message("🚀 Patrick is online and ready!")
    patrick.post_step_completion("Test Step", "This is a test completion message")
    patrick.post_step_failure("Test Failure", ["Violation 1", "Violation 2"], "Test error details")


if __name__ == "__main__":
    main()