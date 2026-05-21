import Landing from "../../pages/garim/Landing";
import Pricing from "../../pages/garim/Pricing";
import Faq from "../../pages/garim/Faq";
import Terms from "../../pages/garim/Terms";
import Signup from "../../pages/garim/Signup";
import Login from "../../pages/garim/Login";
import PasswordReset from "../../pages/garim/PasswordReset";
import Upload from "../../pages/garim/Upload";
import AnalysisProgress from "../../pages/garim/AnalysisProgress";
import AnalysisReport from "../../pages/garim/AnalysisReport";
import SnsConnect from "../../pages/garim/SnsConnect";
import SnsResults from "../../pages/garim/SnsResults";
import PaymentGate from "../../pages/garim/PaymentGate";
import Payment from "../../pages/garim/Payment";
import ReplaceOptions from "../../pages/garim/ReplaceOptions";
import Preview from "../../pages/garim/Preview";
import Processing from "../../pages/garim/Processing";
import Download from "../../pages/garim/Download";
import Dashboard from "../../pages/garim/Dashboard";
import History from "../../pages/garim/History";
import Billing from "../../pages/garim/Billing";
import Settings from "../../pages/garim/Settings";
import LearningConsent from "../../pages/garim/LearningConsent";
import FaceWhitelist from "../../pages/garim/FaceWhitelist";
import AdminAbuse from "../../pages/garim/AdminAbuse";
import AdminQueue from "../../pages/garim/AdminQueue";
import AdminCompliance from "../../pages/garim/AdminCompliance";

export const garimPages = [
  { path: "/", name: "Landing", component: Landing, file: "01-landing.html", layout: "public", current: "landing" },
  { path: "/pricing", name: "Pricing", component: Pricing, file: "02-pricing.html", layout: "public", current: "pricing" },
  { path: "/faq", name: "Faq", component: Faq, file: "03-faq.html", layout: "public", current: "help" },
  { path: "/terms", name: "Terms", component: Terms, file: "04-terms.html", layout: "public", current: "help" },
  { path: "/signup", name: "Signup", component: Signup, file: "05-signup.html", layout: "auth", current: "" },
  { path: "/login", name: "Login", component: Login, file: "06-login.html", layout: "auth", current: "" },
  { path: "/password-reset", name: "PasswordReset", component: PasswordReset, file: "07-password-reset.html", layout: "auth", current: "" },
  { path: "/upload", name: "Upload", component: Upload, file: "08-upload.html", layout: "app", current: "detect" },
  { path: "/analysis-progress", name: "AnalysisProgress", component: AnalysisProgress, file: "09-analysis-progress.html", layout: "app", current: "detect" },
  { path: "/analysis-report", name: "AnalysisReport", component: AnalysisReport, file: "10-analysis-report.html", layout: "app", current: "detect" },
  { path: "/sns-connect", name: "SnsConnect", component: SnsConnect, file: "11-sns-connect.html", layout: "app", current: "sns" },
  { path: "/sns-results", name: "SnsResults", component: SnsResults, file: "12-sns-results.html", layout: "app", current: "sns" },
  { path: "/payment-gate", name: "PaymentGate", component: PaymentGate, file: "13-payment-gate.html", layout: "app", current: "pricing" },
  { path: "/payment", name: "Payment", component: Payment, file: "14-payment.html", layout: "app", current: "pricing" },
  { path: "/replace-options", name: "ReplaceOptions", component: ReplaceOptions, file: "15-replace-options.html", layout: "app", current: "detect" },
  { path: "/preview", name: "Preview", component: Preview, file: "16-preview.html", layout: "app", current: "detect" },
  { path: "/processing", name: "Processing", component: Processing, file: "17-processing.html", layout: "app", current: "detect" },
  { path: "/download", name: "Download", component: Download, file: "18-download.html", layout: "app", current: "detect" },
  { path: "/dashboard", name: "Dashboard", component: Dashboard, file: "19-dashboard.html", layout: "app", current: "dashboard" },
  { path: "/history", name: "History", component: History, file: "20-history.html", layout: "app", current: "history" },
  { path: "/billing", name: "Billing", component: Billing, file: "21-billing.html", layout: "app", current: "billing" },
  { path: "/settings", name: "Settings", component: Settings, file: "22-settings.html", layout: "app", current: "settings" },
  { path: "/learning-consent", name: "LearningConsent", component: LearningConsent, file: "23-learning-consent.html", layout: "app", current: "settings" },
  { path: "/face-whitelist", name: "FaceWhitelist", component: FaceWhitelist, file: "24-face-whitelist.html", layout: "app", current: "settings" },
  { path: "/admin/abuse", name: "AdminAbuse", component: AdminAbuse, file: "25-admin-abuse.html", layout: "admin", current: "abuse" },
  { path: "/admin/queue", name: "AdminQueue", component: AdminQueue, file: "26-admin-queue.html", layout: "admin", current: "queue" },
  { path: "/admin/compliance", name: "AdminCompliance", component: AdminCompliance, file: "27-admin-compliance.html", layout: "admin", current: "compliance" }
];
