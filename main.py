import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from loguru import logger

from scheduler.logger import setup_logger
from scheduler.models import ScheduleRequest, ScheduleResponse
from scheduler.orchestrator import Orchestrator

# Load environment
load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")
ENABLE_FILE_LOGGING = os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure logging
setup_logger(
    enable_file_logging=ENABLE_FILE_LOGGING,
    log_level=LOG_LEVEL
)

if not XAI_API_KEY:
    logger.error("XAI_API_KEY not found in environment")
    raise ValueError("XAI_API_KEY must be set in .env file")

# Initialize FastAPI
app = FastAPI(
    title="AI Staff Scheduler",
    description="Agentic AI-powered staff scheduling system with xAI Grok",
    version="1.0.0"
)

# Initialize orchestrator
orchestrator = Orchestrator(xai_api_key=XAI_API_KEY)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI Staff Scheduler",
        "status": "operational",
        "version": "1.0.0"
    }


@app.post("/schedule", response_model=ScheduleResponse)
async def create_schedule(request: ScheduleRequest):
    """
    Create an optimal staff schedule using agentic AI architecture.

    Flow:
    1. Orchestrator receives a request
    2. Planner creates execution strategy
    3. Executor runs the plan using Scheduler and Lawyer tools
    4. Reviewer validates quality
    5. Returns curated assignments
    """
    try:
        logger.info(f"Received schedule request: {len(request.employees)} employees, {len(request.tasks)} tasks")

        # Validate input
        if not request.employees:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one employee required"
            )

        if not request.tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one task required"
            )

        # Process through orchestrator
        response = await orchestrator.process_schedule_request(request)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal scheduling error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "orchestrator": "ready",
            "xai_api": "configured" if XAI_API_KEY else "missing"
        }
    }

# offline dev
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )