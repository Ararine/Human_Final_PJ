from pathlib import Path


PROGRESS_PAGE = Path("frontend/src/pages/garim/AnalysisProgress.jsx")
UPLOAD_PAGE = Path("frontend/src/pages/garim/Upload.jsx")
API_FILE = Path("frontend/src/utils/api.js")
LANDING_PAGE = Path("frontend/src/pages/garim/Landing.jsx")
PRICING_PAGE = Path("frontend/src/pages/garim/Pricing.jsx")
PRICING_HOOK = Path("frontend/src/hooks/usePricingPlans.js")
HEADER_COMPONENT = Path("frontend/src/components/garim/GarimHeader.jsx")


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

    assert "productType=subscription" in pricing or "productType: isCredit" in pricing
    assert "productType=credit" in pricing or 'productType: "credit"' in pricing
    assert "product_type" in payment
    assert "product_code" in payment
