from fastapi import APIRouter

from controllers import admin, oauth

router = APIRouter(tags=["admin"])

router.add_api_route("/users", admin.list_users, methods=["GET"])
router.add_api_route("/users/{user_id}", oauth.update_user_role_and_status, methods=["PATCH"])
router.add_api_route("/policy", admin.get_policy_settings, methods=["GET"])
router.add_api_route("/policy", admin.update_policy_settings, methods=["PUT"])
router.add_api_route("/plans", admin.list_subscription_plans, methods=["GET"])
router.add_api_route("/plans", admin.create_subscription_plan, methods=["POST"])
router.add_api_route("/plans/{plan_id}", admin.update_subscription_plan, methods=["PUT"])
router.add_api_route("/plans/{plan_id}", admin.delete_subscription_plan, methods=["DELETE"])
router.add_api_route("/credit-plans", admin.list_credit_plans, methods=["GET"])
router.add_api_route("/credit-plans", admin.create_credit_plan, methods=["POST"])
router.add_api_route("/credit-plans/{credit_plan_id}", admin.update_credit_plan, methods=["PUT"])
router.add_api_route("/credit-plans/{credit_plan_id}", admin.delete_credit_plan, methods=["DELETE"])
router.add_api_route("/subscriptions", admin.list_admin_subscriptions, methods=["GET"])
router.add_api_route("/subscriptions/{user_id}", admin.get_admin_subscription_detail, methods=["GET"])
router.add_api_route("/payments", admin.list_payments, methods=["GET"])
router.add_api_route("/payments/{payment_id}", admin.get_payment_detail, methods=["GET"])
router.add_api_route("/payments/{payment_id}/refund", admin.refund_payment, methods=["POST"])
router.add_api_route("/login-histories", admin.list_login_histories, methods=["GET"])
router.add_api_route("/login-histories/export", admin.export_login_histories_csv, methods=["GET"])
router.add_api_route("/login-histories/{login_history_id}", admin.get_login_history_detail, methods=["GET"])



