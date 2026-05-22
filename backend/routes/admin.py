from fastapi import APIRouter

from controllers import admin

router = APIRouter(tags=["admin"])

router.add_api_route("/users", admin.list_users, methods=["GET"])
