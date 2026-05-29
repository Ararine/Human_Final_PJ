from fastapi import APIRouter

from controllers import admin

router = APIRouter(tags=["admin"])

router.add_api_route("/users", admin.list_users, methods=["GET"])
router.add_api_route("/policy", admin.get_policy_settings, methods=["GET"])
router.add_api_route("/policy", admin.update_policy_settings, methods=["PUT"])
