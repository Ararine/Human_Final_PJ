from fastapi import APIRouter

from controllers import analysis

router = APIRouter(tags=["analysis"])
router.add_api_route("/jobs", analysis.create_job_handler, methods=["POST"])
router.add_api_route("/jobs/{job_id}", analysis.get_job_handler, methods=["GET"])
router.add_api_route("/jobs/{job_id}/cancel", analysis.cancel_job_handler, methods=["POST"])
