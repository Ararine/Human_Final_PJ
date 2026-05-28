from fastapi import APIRouter

from controllers import uploads

router = APIRouter(tags=["uploads"])
router.add_api_route("", uploads.create_upload, methods=["POST"])
