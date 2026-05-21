from fastapi import APIRouter

from controllers import setting

router = APIRouter(tags=["settings"])

router.add_api_route(
    "/{user_id}",
    setting.get_setting,
    methods=["GET"]
)

router.add_api_route(
    "/{user_id}",
    setting.update_setting,
    methods=["PUT"]
)

