"""
BareMetal Match

A multi-agent system built with CrewAI and Claude that automates embedded
software engineering job searching, skills analysis, interview preparation,
and career advisory.

Originally built as "Job Search AI Agent System" by Claude Builder Club @ UC
Irvine (Intro to AI Agents Workshop, October 20, 2025).
"""

__version__ = "1.0.0"
__author__ = "Aniket Londhe"

# Export main components for easy importing
from src.agents import (
    create_job_searcher_agent,
    create_skills_advisor_agent,
    create_interview_coach_agent,
    create_career_advisor_agent,
    create_all_agents,
)

from src.tasks import (
    create_job_search_task,
    create_skills_analysis_task,
    create_interview_prep_task,
    create_career_advisory_task,
    create_all_tasks,
)

from src.tools import search_jobs

from src.config import (
    DEFAULT_JOB_ROLE,
    DEFAULT_LOCATION,
    DEFAULT_NUM_RESULTS,
    validate_config,
)

__all__ = [
    # Agents
    "create_job_searcher_agent",
    "create_skills_advisor_agent",
    "create_interview_coach_agent",
    "create_career_advisor_agent",
    "create_all_agents",
    # Tasks
    "create_job_search_task",
    "create_skills_analysis_task",
    "create_interview_prep_task",
    "create_career_advisory_task",
    "create_all_tasks",
    # Tools
    "search_jobs",
    # Config
    "DEFAULT_JOB_ROLE",
    "DEFAULT_LOCATION",
    "DEFAULT_NUM_RESULTS",
    "validate_config",
]
