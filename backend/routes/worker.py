from fastapi import APIRouter

from controllers import worker

router = APIRouter(tags=["worker"])
router.add_api_route("/jobs/next", worker.get_next_job_handler, methods=["GET"])
router.add_api_route("/jobs/{job_id}/accept", worker.accept_job_handler, methods=["POST"])
router.add_api_route("/jobs/{job_id}/progress", worker.update_progress_handler, methods=["PUT"])
router.add_api_route("/jobs/{job_id}/complete", worker.complete_job_handler, methods=["POST"])
router.add_api_route("/jobs/{job_id}/fail", worker.fail_job_handler, methods=["POST"])
router.add_api_route("/files/{upload_id}", worker.get_file_handler, methods=["GET"])
router.add_api_route("/heartbeat", worker.heartbeat_handler, methods=["POST"])
