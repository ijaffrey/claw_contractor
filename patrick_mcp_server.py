import asyncio
import json
import uuid
import threading
import subprocess
import sys
import os
from datetime import datetime
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

JOB_STORE = {}

server = Server("patrick-mcp-server")

def run_patrick_in_background(job_id: str, repo: str, sprint_plan_file: str):
    """Run Patrick in a background thread and update job status"""
    try:
        # Update job status to running
        JOB_STORE[job_id]["status"] = "running"
        JOB_STORE[job_id]["started_at"] = datetime.now().isoformat()
        
        # Run Patrick command
        cmd = ["python", "-m", "patrick.main", "--sprint-plan", sprint_plan_file, "--repo", repo]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        # Update job status with results
        JOB_STORE[job_id]["status"] = "completed" if result.returncode == 0 else "failed"
        JOB_STORE[job_id]["completed_at"] = datetime.now().isoformat()
        JOB_STORE[job_id]["return_code"] = result.returncode
        JOB_STORE[job_id]["stdout"] = result.stdout
        JOB_STORE[job_id]["stderr"] = result.stderr
        
    except subprocess.TimeoutExpired:
        JOB_STORE[job_id]["status"] = "timeout"
        JOB_STORE[job_id]["completed_at"] = datetime.now().isoformat()
        JOB_STORE[job_id]["error"] = "Process timed out after 1 hour"
    except Exception as e:
        JOB_STORE[job_id]["status"] = "error"
        JOB_STORE[job_id]["completed_at"] = datetime.now().isoformat()
        JOB_STORE[job_id]["error"] = str(e)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="run_sprint",
            description="Run a Patrick sprint with the provided plan and repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_plan": {
                        "type": "object",
                        "description": "The sprint plan configuration as a dictionary"
                    },
                    "repo": {
                        "type": "string", 
                        "description": "Path to the repository to work on"
                    }
                },
                "required": ["sprint_plan", "repo"]
            },
        ),
        types.Tool(
            name="get_status",
            description="Get the status of a Patrick sprint job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The unique job ID returned from run_sprint"
                    }
                },
                "required": ["job_id"]
            },
        ),
        types.Tool(
            name="list_jobs",
            description="List all Patrick sprint jobs and their statuses",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
        ),
        types.Tool(
            name="say_hello",
            description="A simple greeting tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to greet"
                    }
                },
                "required": ["name"]
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "run_sprint":
        if not arguments:
            raise ValueError("Missing arguments")
        
        sprint_plan = arguments.get("sprint_plan")
        repo = arguments.get("repo")
        
        if not sprint_plan or not repo:
            raise ValueError("Both sprint_plan and repo are required")
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save sprint plan to temporary file
        sprint_plan_file = f"/tmp/patrick_job_{job_id}.json"
        try:
            with open(sprint_plan_file, 'w') as f:
                json.dump(sprint_plan, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save sprint plan: {str(e)}")
        
        # Initialize job in store
        JOB_STORE[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "repo": repo,
            "sprint_plan_file": sprint_plan_file,
            "sprint_plan": sprint_plan
        }
        
        # Start Patrick in background thread
        thread = threading.Thread(
            target=run_patrick_in_background,
            args=(job_id, repo, sprint_plan_file),
            daemon=True
        )
        thread.start()
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "job_id": job_id,
                    "status": "queued",
                    "message": f"Sprint job {job_id} has been queued and will start shortly"
                }, indent=2)
            )
        ]
    
    elif name == "get_status":
        if not arguments:
            raise ValueError("Missing arguments")
        
        job_id = arguments.get("job_id")
        if not job_id:
            raise ValueError("job_id is required")
        
        if job_id not in JOB_STORE:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Job {job_id} not found"
                    }, indent=2)
                )
            ]
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(JOB_STORE[job_id], indent=2)
            )
        ]
    
    elif name == "list_jobs":
        return [
            types.TextContent(
                type="text",
                text=json.dumps(list(JOB_STORE.values()), indent=2)
            )
        ]
    
    elif name == "say_hello":
        if not arguments:
            raise ValueError("Missing arguments")
        
        name_arg = arguments.get("name", "World")
        return [
            types.TextContent(
                type="text", 
                text=f"Hello, {name_arg}! This is Patrick MCP Server."
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="patrick-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())