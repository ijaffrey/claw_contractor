import subprocess
import json
import re
from typing import Dict, List, Optional, Any


class Agents:
    """
    Agents class for managing AI agents and executing acceptance criteria.
    """

    def __init__(self, api_key: str):
        """
        Initialize the Agents class with API key.

        Args:
            api_key (str): API key for authentication
        """
        self.api_key = api_key
        self.agents = {}

    def create_agent(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Create a new agent with given configuration.

        Args:
            name (str): Agent name
            config (Dict[str, Any]): Agent configuration

        Returns:
            bool: True if agent created successfully, False otherwise
        """
        try:
            self.agents[name] = {
                "config": config,
                "status": "active",
                "created_at": subprocess.run(
                    ["date"], capture_output=True, text=True
                ).stdout.strip(),
            }
            return True
        except Exception as e:
            print(f"Error creating agent {name}: {e}")
            return False

    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent by name.

        Args:
            name (str): Agent name

        Returns:
            Optional[Dict[str, Any]]: Agent configuration or None if not found
        """
        return self.agents.get(name)

    def list_agents(self) -> List[str]:
        """
        List all agent names.

        Returns:
            List[str]: List of agent names
        """
        return list(self.agents.keys())

    def run_acceptance_criteria(
        self, criteria: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute shell commands from acceptance criteria.

        Args:
            criteria (str): Acceptance criteria text containing shell commands
            timeout (int): Command execution timeout in seconds

        Returns:
            Dict[str, Any]: Execution results with status, output, and errors
        """
        results = {
            "status": "success",
            "executed_commands": [],
            "outputs": [],
            "errors": [],
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
        }

        try:
            # Parse shell commands from criteria
            commands = self._parse_shell_commands(criteria)
            results["total_commands"] = len(commands)

            if not commands:
                results["status"] = "no_commands"
                results["errors"].append(
                    "No shell commands found in acceptance criteria"
                )
                return results

            # Execute each command
            for i, command in enumerate(commands):
                command_result = self._execute_shell_command(command, timeout)

                results["executed_commands"].append(command)
                results["outputs"].append(command_result["output"])

                if command_result["success"]:
                    results["successful_commands"] += 1
                else:
                    results["failed_commands"] += 1
                    results["errors"].append(
                        f"Command {i+1} failed: {command_result['error']}"
                    )

            # Set overall status
            if results["failed_commands"] > 0:
                results["status"] = (
                    "partial_failure"
                    if results["successful_commands"] > 0
                    else "failure"
                )

        except Exception as e:
            results["status"] = "error"
            results["errors"].append(f"Unexpected error: {str(e)}")

        return results

    def _parse_shell_commands(self, criteria: str) -> List[str]:
        """
        Parse shell commands from acceptance criteria text.

        Args:
            criteria (str): Acceptance criteria text

        Returns:
            List[str]: List of shell commands found
        """
        commands = []

        # Pattern 1: Commands in code blocks (```bash or ```shell or ```)
        code_block_patterns = [
            r"```(?:bash|shell|sh)\s*\n(.*?)\n```",
            r"```\s*\n(.*?)\n```",
        ]

        for pattern in code_block_patterns:
            matches = re.findall(pattern, criteria, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split multi-line commands
                lines = match.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        commands.append(line)

        # Pattern 2: Commands prefixed with $ or >
        command_patterns = [r"^\s*\$\s+(.+)$", r"^\s*>\s+(.+)$"]

        for pattern in command_patterns:
            matches = re.findall(pattern, criteria, re.MULTILINE)
            for match in matches:
                if match.strip():
                    commands.append(match.strip())

        # Pattern 3: Commands in backticks
        backtick_pattern = r"`([^`]+)`"
        matches = re.findall(backtick_pattern, criteria)
        for match in matches:
            # Only consider it a command if it contains typical command keywords
            if any(
                keyword in match.lower()
                for keyword in [
                    "ls",
                    "cd",
                    "cat",
                    "grep",
                    "find",
                    "echo",
                    "mkdir",
                    "rm",
                    "cp",
                    "mv",
                    "chmod",
                    "chown",
                    "ps",
                    "kill",
                    "curl",
                    "wget",
                    "git",
                ]
            ):
                commands.append(match.strip())

        # Remove duplicates while preserving order
        unique_commands = []
        seen = set()
        for cmd in commands:
            if cmd not in seen:
                unique_commands.append(cmd)
                seen.add(cmd)

        return unique_commands

    def _execute_shell_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """
        Execute a single shell command.

        Args:
            command (str): Shell command to execute
            timeout (int): Execution timeout in seconds

        Returns:
            Dict[str, Any]: Command execution result
        """
        result = {
            "success": False,
            "output": "",
            "error": "",
            "return_code": None,
            "command": command,
        }

        try:
            # Security check - prevent dangerous commands
            dangerous_patterns = [
                r"\brm\s+-rf\s+/",
                r"\bformat\b",
                r"\bdel\s+/[sq]",
                r">\s*/dev/sda",
                r"\bdd\s+if=",
                r"\bmkfs\b",
                r"\bshutdown\b",
                r"\breboot\b",
                r"\binit\s+0",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    result["error"] = f"Dangerous command blocked: {command}"
                    return result

            # Execute command
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd="/tmp",  # Safe working directory
            )

            result["success"] = process.returncode == 0
            result["output"] = process.stdout
            result["error"] = process.stderr
            result["return_code"] = process.returncode

        except subprocess.TimeoutExpired:
            result["error"] = f"Command timed out after {timeout} seconds"
        except subprocess.CalledProcessError as e:
            result["error"] = (
                f"Command failed with return code {e.returncode}: {e.stderr}"
            )
            result["return_code"] = e.returncode
        except Exception as e:
            result["error"] = f"Unexpected error executing command: {str(e)}"

        return result

    def validate_criteria(self, criteria: str) -> Dict[str, Any]:
        """
        Validate acceptance criteria format and commands.

        Args:
            criteria (str): Acceptance criteria to validate

        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "command_count": 0,
            "dangerous_commands": [],
        }

        try:
            commands = self._parse_shell_commands(criteria)
            validation["command_count"] = len(commands)

            if not commands:
                validation["warnings"].append(
                    "No shell commands found in acceptance criteria"
                )

            # Check for potentially dangerous commands
            dangerous_patterns = {
                r"\brm\s+-rf": "Recursive force delete",
                r"\bformat\b": "Format command",
                r"\bdd\s+": "Low-level disk operation",
                r"\bmkfs\b": "Filesystem creation",
                r"\bshutdown\b": "System shutdown",
                r"\breboot\b": "System reboot",
            }

            for command in commands:
                for pattern, description in dangerous_patterns.items():
                    if re.search(pattern, command, re.IGNORECASE):
                        validation["dangerous_commands"].append(
                            {"command": command, "reason": description}
                        )

            if validation["dangerous_commands"]:
                validation["valid"] = False
                validation["errors"].append("Dangerous commands detected")

        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Validation error: {str(e)}")

        return validation
