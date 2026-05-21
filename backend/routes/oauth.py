from fastapi import APIRouter

from controllers import oauth


router = APIRouter(tags=["auth"])
router.add_api_route("/{provider}/start", oauth.start_oauth, methods=["GET"])
router.add_api_route("/{provider}/callback", oauth.oauth_callback, methods=["GET"])
router.add_api_route("/me", oauth.get_me, methods=["GET"])
router.add_api_route("/logout", oauth.logout, methods=["POST"])
