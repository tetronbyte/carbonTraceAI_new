# Job/Task tracking system with MongoDB persistence
# 
# NOTE: This module is deprecated in favor of services/job_tracker.py
# It's kept for backward compatibility only.
# 
# New code should import from services.job_tracker:
#   from services.job_tracker import job_tracker, job_store
#
from services.job_tracker import job_store, job_tracker

# Export for backward compatibility
__all__ = ['job_store', 'job_tracker']


