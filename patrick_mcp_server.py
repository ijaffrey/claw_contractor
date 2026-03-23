import asyncio
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job:
    def __init__(self, job_id: str, job_type: str, data: Dict[str, Any]):
        self.job_id = job_id
        self.job_type = job_type
        self.data = data
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.guidance = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "guidance": self.guidance
        }

# Global job storage
jobs: Dict[str, Job] = {}
server_start_time = datetime.now()

def run_sprint(sprint_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a sprint and returns results.
    
    Args:
        sprint_data: Dictionary containing sprint configuration
        
    Returns:
        Dict containing sprint execution results
    """
    try:
        # Validate sprint data
        if not isinstance(sprint_data, dict):
            raise ValueError("sprint_data must be a dictionary")
            
        required_fields = ["name", "tasks", "duration"]
        for field in required_fields:
            if field not in sprint_data:
                raise ValueError(f"Missing required field: {field}")
        
        job_id = str(uuid.uuid4())
        job = Job(job_id, "sprint", sprint_data)
        jobs[job_id] = job
        
        # Start job execution
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # Simulate sprint execution
        tasks = sprint_data.get("tasks", [])
        completed_tasks = []
        failed_tasks = []
        
        for task in tasks:
            try:
                # Simulate task execution
                task_result = {
                    "task_id": task.get("id", str(uuid.uuid4())),
                    "name": task.get("name", "Unnamed Task"),
                    "status": "completed",
                    "duration": task.get("estimated_duration", 1),
                    "result": f"Task '{task.get('name', 'Unnamed')}' completed successfully"
                }
                completed_tasks.append(task_result)
            except Exception as e:
                failed_task = {
                    "task_id": task.get("id", str(uuid.uuid4())),
                    "name": task.get("name", "Unnamed Task"),
                    "status": "failed",
                    "error": str(e)
                }
                failed_tasks.append(failed_task)
        
        # Complete job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        
        result = {
            "job_id": job_id,
            "sprint_name": sprint_data.get("name"),
            "status": "completed",
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "completed_task_details": completed_tasks,
            "failed_task_details": failed_tasks,
            "started_at": job.started_at.isoformat(),
            "completed_at": job.completed_at.isoformat(),
            "duration": (job.completed_at - job.started_at).total_seconds()
        }
        
        job.result = result
        return result
        
    except Exception as e:
        logger.error(f"Error running sprint: {str(e)}")
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
        
        return {
            "status": "failed",
            "error": str(e),
            "job_id": job_id if 'job_id' in locals() else None
        }

def get_status(job_id: str) -> Dict[str, Any]:
    """
    Returns status of a job.
    
    Args:
        job_id: Unique identifier of the job
        
    Returns:
        Dict containing job status information
    """
    try:
        if not job_id:
            raise ValueError("job_id is required")
            
        if job_id not in jobs:
            return {
                "status": "not_found",
                "error": f"Job with ID {job_id} not found",
                "job_id": job_id
            }
        
        job = jobs[job_id]
        return job.to_dict()
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "job_id": job_id
        }

def send_guidance(job_id: str, guidance: str) -> Dict[str, Any]:
    """
    Sends guidance to a running job.
    
    Args:
        job_id: Unique identifier of the job
        guidance: Guidance message to send
        
    Returns:
        Dict containing operation result
    """
    try:
        if not job_id:
            raise ValueError("job_id is required")
            
        if not guidance:
            raise ValueError("guidance is required")
            
        if job_id not in jobs:
            return {
                "status": "failed",
                "error": f"Job with ID {job_id} not found",
                "job_id": job_id
            }
        
        job = jobs[job_id]
        
        if job.status != JobStatus.RUNNING:
            return {
                "status": "failed",
                "error": f"Job {job_id} is not running. Current status: {job.status.value}",
                "job_id": job_id
            }
        
        guidance_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": guidance,
            "id": str(uuid.uuid4())
        }
        
        job.guidance.append(guidance_entry)
        
        return {
            "status": "success",
            "message": "Guidance sent successfully",
            "job_id": job_id,
            "guidance_id": guidance_entry["id"]
        }
        
    except Exception as e:
        logger.error(f"Error sending guidance: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "job_id": job_id
        }

def list_jobs() -> Dict[str, Any]:
    """
    Returns list of all jobs.
    
    Returns:
        Dict containing list of all jobs
    """
    try:
        job_list = []
        for job in jobs.values():
            job_summary = {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            job_list.append(job_summary)
        
        # Sort by creation time, newest first
        job_list.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "success",
            "total_jobs": len(job_list),
            "jobs": job_list
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "jobs": []
        }

def health_check() -> Dict[str, Any]:
    """
    Returns server health status.
    
    Returns:
        Dict containing server health information
    """
    try:
        current_time = datetime.now()
        uptime = (current_time - server_start_time).total_seconds()
        
        # Count jobs by status
        status_counts = {status.value: 0 for status in JobStatus}
        for job in jobs.values():
            status_counts[job.status.value] += 1
        
        return {
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "uptime_seconds": uptime,
            "total_jobs": len(jobs),
            "job_status_counts": status_counts,
            "memory_usage": {
                "jobs_in_memory": len(jobs)
            },
            "server_info": {
                "name": "Patrick MCP Server",
                "version": "1.0.0",
                "started_at": server_start_time.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def generate_and_run(prompt: str) -> Dict[str, Any]:
    """
    Generates and executes code from prompt.
    
    Args:
        prompt: Natural language prompt describing the task
        
    Returns:
        Dict containing generation and execution results
    """
    try:
        if not prompt:
            raise ValueError("prompt is required")
            
        job_id = str(uuid.uuid4())
        job = Job(job_id, "generate_and_run", {"prompt": prompt})
        jobs[job_id] = job
        
        # Start job execution
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # Simulate code generation
        generated_code = f"""
# Generated code for: {prompt}
def generated_function():
    '''
    This function was generated based on the prompt: {prompt}
    '''
    result = "Code generated and executed successfully"
    print(f"Executing task: {prompt}")
    return result

# Execute the generated function
if __name__ == "__main__":
    output = generated_function()
    print(output)
"""
        
        # Simulate code execution
        execution_result = {
            "stdout": f"Executing task: {prompt}\nCode generated and executed successfully",
            "stderr": "",
            "return_code": 0,
            "execution_time": 0.1
        }
        
        # Complete job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        
        result = {
            "job_id": job_id,
            "status": "completed",
            "prompt": prompt,
            "generated_code": generated_code,
            "execution_result": execution_result,
            "started_at": job.started_at.isoformat(),
            "completed_at": job.completed_at.isoformat(),
            "duration": (job.completed_at - job.started_at).total_seconds()
        }
        
        job.result = result
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_and_run: {str(e)}")
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
        
        return {
            "status": "failed",
            "error": str(e),
            "job_id": job_id if 'job_id' in locals() else None,
            "traceback": traceback.format_exc()
        }

# Utility functions for job management
def cancel_job(job_id: str) -> Dict[str, Any]:
    """
    Cancels a running job.
    
    Args:
        job_id: Unique identifier of the job to cancel
        
    Returns:
        Dict containing cancellation result
    """
    try:
        if job_id not in jobs:
            return {
                "status": "failed",
                "error": f"Job with ID {job_id} not found"
            }
        
        job = jobs[job_id]
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return {
                "status": "failed",
                "error": f"Job {job_id} cannot be cancelled. Current status: {job.status.value}"
            }
        
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        
        return {
            "status": "success",
            "message": f"Job {job_id} cancelled successfully",
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def cleanup_completed_jobs(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Removes completed jobs older than specified age.
    
    Args:
        max_age_hours: Maximum age of completed jobs to keep in hours
        
    Returns:
        Dict containing cleanup results
    """
    try:
        current_time = datetime.now()
        removed_count = 0
        
        jobs_to_remove = []
        for job_id, job in jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at:
                    age_hours = (current_time - job.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del jobs[job_id]
            removed_count += 1
        
        return {
            "status": "success",
            "removed_jobs": removed_count,
            "remaining_jobs": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }