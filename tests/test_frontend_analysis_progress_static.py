from pathlib import Path


PROGRESS_PAGE = Path("frontend/src/pages/garim/AnalysisProgress.jsx")
UPLOAD_PAGE = Path("frontend/src/pages/garim/Upload.jsx")
API_FILE = Path("frontend/src/utils/api.js")
LANDING_PAGE = Path("frontend/src/pages/garim/Landing.jsx")
PRICING_PAGE = Path("frontend/src/pages/garim/Pricing.jsx")
PRICING_HOOK = Path("frontend/src/hooks/usePricingPlans.js")
HEADER_COMPONENT = Path("frontend/src/components/garim/GarimHeader.jsx")
ADMIN_POLICY_PAGE = Path("frontend/src/pages/garim/AdminPolicy.jsx")
ADMIN_SERVICE = Path("backend/services/admin.py")


def test_analysis_progress_uses_live_job_polling():
    source = PROGRESS_PAGE.read_text(encoding="utf-8")

    assert "getAnalysisJob" in source
    assert "useLocation" in source
    assert "useSearchParams" in source
    assert "setInterval" in source
    assert "family_picnic_2026.mp4" not in source
    assert 'width: "46%"' not in source
    assert "46%" not in source


def test_upload_navigates_with_job_context():
    source = UPLOAD_PAGE.read_text(encoding="utf-8")

    assert "jobId" in source
    assert "uploadId" in source
    assert "fileName" in source
    assert "fileSize" in source
    assert "/analysis-progress?jobId=" in source


def test_api_exposes_analysis_cancel():
    source = API_FILE.read_text(encoding="utf-8")

    assert "export async function cancelAnalysisJob" in source
    assert "/analysis/jobs/${jobId}/cancel" in source


def test_landing_and_pricing_share_plan_source():
    landing = LANDING_PAGE.read_text(encoding="utf-8")
    pricing = PRICING_PAGE.read_text(encoding="utf-8")
    hook = PRICING_HOOK.read_text(encoding="utf-8")

    assert "usePricingPlans" in landing
    assert "usePricingPlans" in pricing
    assert "export function usePricingPlans" in hook
    assert "1회권" not in landing
    assert "MVP1 단계에서는 모든 기능이 무료입니다" not in landing


def test_header_logo_always_links_home():
    source = HEADER_COMPONENT.read_text(encoding="utf-8")

    assert 'to={isAuthed ? "/dashboard" : "/"}' not in source
    assert '<Link to="/" className="gh__logo">' in source


def test_login_next_paths_are_preserved_for_action_buttons():
    header = HEADER_COMPONENT.read_text(encoding="utf-8")
    landing = LANDING_PAGE.read_text(encoding="utf-8")
    pricing = PRICING_PAGE.read_text(encoding="utf-8")
    api = API_FILE.read_text(encoding="utf-8")

    assert "buildLoginUrl(item.to)" in header
    assert 'buildLoginUrl("/upload")' in header
    assert '`/login?next=${encodeURIComponent("/upload")}`' in landing
    assert "`/login?next=${encodeURIComponent(paymentPath)}`" in pricing
    assert "getOAuthStartUrl(provider, nextPath = \"\")" in api


PAYMENT_PAGE = Path("frontend/src/pages/garim/Payment.jsx")


def test_pricing_uses_product_type_url_params():
    pricing = PRICING_PAGE.read_text(encoding="utf-8")
    payment = PAYMENT_PAGE.read_text(encoding="utf-8")
    hook = PRICING_HOOK.read_text(encoding="utf-8")

    assert "productType=subscription" in pricing or "productType: isCredit" in pricing
    assert (
        "productType=credit" in pricing
        or 'productType: "credit"' in pricing
        or 'productType: "credit"' in hook
    )
    assert "product_type" in payment
    assert "product_code" in payment


def test_pricing_uses_active_sorted_admin_plans():
    pricing = PRICING_PAGE.read_text(encoding="utf-8")
    hook = PRICING_HOOK.read_text(encoding="utf-8")
    admin_service = ADMIN_SERVICE.read_text(encoding="utf-8")

    assert "sortOrder" in hook
    assert "badgeLabel" in hook
    assert "badgeClass" in hook
    assert "ctaLabel" not in hook
    assert "payment.description || meta.description" in hook
    assert "isActive" not in hook
    assert "status" in hook
    assert ".filter((plan) => plan.status === \"active\")" in hook
    assert ".sort((a, b) => a.sortOrder - b.sortOrder)" in hook
    assert "buildCreditPlans" in hook
    assert "creditPlans.map" in pricing
    assert 'key: "credit_100"' not in pricing
    assert 'key: "credit_500"' not in pricing
    assert "WHERE is_active = TRUE" not in admin_service
    assert "WHERE status = 'active'" in admin_service
    assert "ORDER BY sort_order ASC, created_at ASC" in admin_service


def test_admin_policy_plan_management_layout():
    source = ADMIN_POLICY_PAGE.read_text(encoding="utf-8")
    api = API_FILE.read_text(encoding="utf-8")

    assert "정책 및 상품 관리" in source
    assert "구독 플랜과 크레딧 플랜의 정책을 설정하고 관리할 수 있습니다." in source
    assert "구독 플랜" in source
    assert "크레딧 플랜" in source
    assert "activeTab" in source
    assert "subscription" in source
    assert "credit" in source
    assert "planSearch" in source
    assert "creditSearch" in source
    assert "subscriptionPage" in source
    assert "subscriptionLimit" in source
    assert "subscriptionTotal" in source
    assert "creditPage" in source
    assert "creditLimit" in source
    assert "creditTotal" in source
    assert "PAGE_LIMIT_OPTIONS" in source
    assert "PlanPagination" in source
    assert "lastPage" in source
    assert "setSubscriptionPage(lastPage)" in source
    assert "setCreditPage(lastPage)" in source
    assert "pol-pagination" in source
    assert "개씩 보기" in source
    assert "이전" in source
    assert "다음" in source
    assert "getAdminPlans" in source
    assert "getAdminCreditPlans" in source
    assert "subscriptionPage" in source
    assert "subscriptionLimit" in source
    assert "creditPage" in source
    assert "creditLimit" in source
    assert "createAdminPlan" in api
    assert "updateAdminPlan" in api
    assert "deleteAdminPlan" in api
    assert "createAdminCreditPlan" in api
    assert "updateAdminCreditPlan" in api
    assert "deleteAdminCreditPlan" in api
    assert "/admin/plans" in api
    assert "/admin/credit-plans" in api
    assert 'query.set("page", params.page)' in api
    assert 'query.set("limit", params.limit)' in api


def test_admin_policy_subscription_plan_form_fields():
    source = ADMIN_POLICY_PAGE.read_text(encoding="utf-8")

    for field in [
        "plan_code",
        "plan_name",
        "badge_label",
        "badge_class",
        "description",
        "monthly_quota",
        "result_retention_days",
        "watermark_required",
        "price_amount",
        "sort_order",
        "status",
        "file_size_limit",
        "max_jobs",
        "auto_delete_original_hours",
        "metadata_retention_days",
        "credits",
    ]:
        assert field in source


    assert "SUBSCRIPTION_NUMBER_FIELDS" in source
    assert '"monthly_quota"' in source
    assert '"result_retention_days"' in source
    assert '"price_amount"' in source
    assert '"sort_order"' in source
    assert '"file_size_limit"' in source
    assert '"max_jobs"' in source
    assert '"auto_delete_original_hours"' in source
    assert '"metadata_retention_days"' in source
    assert '"credits"' in source
    assert '<input\n        type="number"' in source
    assert 'label="워터마크 필수"' in source
    assert 'label="사용자 화면 노출"' not in source
    assert 'label="배지 문구"' in source
    assert "SelectField" in source
    assert "BADGE_CLASS_OPTIONS" in source
    assert 'label="배지 스타일"' in source
    assert '"mui-chip--primary"' in source
    assert '"mui-chip--soft-warning"' in source
    assert 'label="버튼 문구"' not in source
    assert 'label="설명 문구"' in source
    assert "PlanPreviewPanel" in source
    assert "pol-price-preview" in source
    assert "getAdminPlans" in source


def test_admin_policy_credit_plan_form_fields():
    source = ADMIN_POLICY_PAGE.read_text(encoding="utf-8")

    for field in [
        "credit_plan_code",
        "credit_plan_name",
        "price_amount",
        "base_credits",
        "bonus_credits",
        "expires_days",
        "sort_order",
        "status",
    ]:
        assert field in source

    assert "is_active" not in source

    assert "CREDIT_NUMBER_FIELDS" in source
    assert '"price_amount"' in source
    assert '"base_credits"' in source
    assert '"bonus_credits"' in source
    assert '"expires_days"' in source
    assert '"sort_order"' in source
    assert 'label="보너스 크레딧"' in source
    assert 'label="유효 기간"' in source
    assert 'label="사용자 화면 노출"' not in source
    assert "CreditPreviewPanel" in source
    assert "pol-credit-preview" in source
    assert "getAdminCreditPlans" in source
