import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import "../../css/garim-pages/Faq.css";

import GarimPage from "../../components/garim/GarimPage";

const CATEGORIES = [
  { id: "all", label: "전체", icon: "apps" },
  { id: "start", label: "시작하기", icon: "play_arrow" },
  { id: "detect", label: "검출 기능", icon: "visibility" },
  { id: "replace", label: "치환 기능", icon: "visibility_off" },
  { id: "payment", label: "결제·환불", icon: "payment" },
  { id: "security", label: "데이터·보안", icon: "lock" },
  { id: "sns", label: "SNS 연동", icon: "share" },
  { id: "spec", label: "입력 사양", icon: "tune" },
];

const FAQ_ITEMS = [
  {
    category: "start",
    question: "Garim은 어떤 서비스인가요?",
    answer:
      "Garim은 영상, 이미지, 음성 파일에서 개인정보 노출 위험을 찾고 필요한 항목을 마스킹 또는 치환해 결과물을 만드는 서비스입니다. 현재는 파일 업로드 기반 흐름을 중심으로 제공하며, 업로드 후 분석 진행, 탐지 결과 확인, 처리 옵션 선택, 미리보기, 최종 처리 순서로 이용합니다.",
  },
  {
    category: "start",
    question: "처음 이용할 때 어떤 순서로 진행하면 되나요?",
    answer:
      "로그인 후 파일 업로드 화면에서 파일을 선택하고 분석을 시작합니다. 분석이 끝나면 탐지 결과 화면에서 개인정보 후보를 확인하고, 필요한 항목만 선택해 미리보기 또는 최종 마스킹 처리를 진행하면 됩니다. 처리 완료 후에는 결과 페이지에서 다운로드할 수 있습니다.",
  },
  {
    category: "start",
    question: "약관 동의가 필요한 이유는 무엇인가요?",
    answer:
      "업로드 파일 분석과 결과물 생성을 위해 서비스 이용약관과 개인정보 처리 관련 동의가 필요합니다. 필수 동의가 완료되지 않은 사용자는 업로드 단계에서 약관 동의 모달을 먼저 확인하게 됩니다.",
  },
  {
    category: "start",
    question: "분석만 해도 크레딧이 차감되나요?",
    answer:
      "현재 분석 작업 생성 단계에서는 크레딧을 차감하지 않습니다. 프로젝트 코드 기준으로 크레딧은 상세보기 접근이나 유료 처리 기능에서 사용될 수 있도록 분리되어 있습니다.",
  },
  {
    category: "detect",
    question: "어떤 개인정보를 검출하나요?",
    answer:
      "이미지와 영상에서는 화면에 보이는 개인정보 후보를 탐지하고, 음성 또는 영상 음성에서는 STT 분석 흐름을 통해 텍스트 기반 개인정보 후보를 찾습니다. 이름, 연락처, 주소, 차량번호, 신분증, 송장 정보처럼 개인을 식별할 수 있는 항목을 주요 대상으로 봅니다.",
  },
  {
    category: "detect",
    question: "음성 속 이름이나 전화번호도 확인할 수 있나요?",
    answer:
      "네. 영상 또는 음성 파일은 별도 음성 분석 작업을 통해 텍스트로 변환한 뒤 개인정보 후보를 확인하는 흐름이 준비되어 있습니다. 다만 음질, 배경 소음, 발음, 겹치는 음성에 따라 탐지 정확도는 달라질 수 있습니다.",
  },
  {
    category: "detect",
    question: "탐지 결과가 틀리거나 누락되면 어떻게 하나요?",
    answer:
      "탐지 결과 화면에서 항목별로 선택 여부를 조정할 수 있습니다. 필요 없는 항목은 선택 해제하고, 민감하다고 판단되는 항목은 선택해 마스킹 처리하면 됩니다. 오탐이나 누락은 고객센터 및 신고 접수 화면에서 버그 및 오탐지 신고로 전달할 수 있습니다.",
  },
  {
    category: "detect",
    question: "분석 진행 중 상태를 확인할 수 있나요?",
    answer:
      "분석 진행 화면에서 현재 단계, 전체 진행률, 대기 상태를 확인할 수 있습니다. 작업은 업로드 완료 후 분석 작업으로 등록되고, 진행 화면은 작업 상태를 조회해 사용자가 흐름을 계속 확인할 수 있도록 구성되어 있습니다.",
  },
  {
    category: "replace",
    question: "마스킹 처리 전에 결과를 미리 볼 수 있나요?",
    answer:
      "네. 탐지 항목을 선택한 뒤 마스킹 미리보기를 생성할 수 있습니다. 미리보기 단계에서 결과가 어색하거나 누락된 부분이 있으면 이전 단계로 돌아가 선택 항목을 조정한 뒤 다시 진행하면 됩니다.",
  },
  {
    category: "replace",
    question: "모든 탐지 항목이 자동으로 처리되나요?",
    answer:
      "자동으로 탐지 후보를 보여주지만, 최종 처리 대상은 사용자가 선택할 수 있습니다. 선택 저장 API가 별도로 있어 필요한 항목만 처리 대상에 포함할 수 있고, 뒤로가기나 미리보기 정리 시 선택 상태를 초기화하는 흐름도 준비되어 있습니다.",
  },
  {
    category: "replace",
    question: "이미지와 영상 모두 처리할 수 있나요?",
    answer:
      "네. 이미지와 영상 파일을 모두 업로드할 수 있고, 결과 페이지에서는 처리된 파일을 확인하거나 다운로드할 수 있습니다. 영상은 구간 미리보기와 최종 처리 작업이 별도 단계로 이어질 수 있습니다.",
  },
  {
    category: "replace",
    question: "처리 결과가 마음에 들지 않으면 다시 만들 수 있나요?",
    answer:
      "탐지 결과와 선택 항목을 다시 조정한 뒤 미리보기 또는 최종 처리 작업을 다시 실행하는 방식으로 재작업할 수 있습니다. 이미 생성된 미리보기 파일은 뒤로가기나 정리 요청 시 삭제되도록 설계되어 있습니다.",
  },
  {
    category: "payment",
    question: "요금제와 크레딧 상품은 어떻게 다르나요?",
    answer:
      "요금제는 Free, Pro, Studio 같은 구독형 플랜이고, 크레딧 상품은 필요한 만큼 별도로 충전하는 상품입니다. Pricing 화면에서는 구독 플랜과 크레딧 상품을 각각 확인하고 결제할 수 있습니다.",
  },
  {
    category: "payment",
    question: "월 결제와 연 결제는 어떻게 표시되나요?",
    answer:
      "구독 플랜은 월 결제와 연 결제 기준으로 금액과 제공 크레딧을 확인할 수 있도록 구성되어 있습니다. 연 결제 값이 따로 없으면 월 금액의 10개월분, 제공 크레딧의 12개월분 기준으로 계산하는 로직을 유지합니다.",
  },
  {
    category: "payment",
    question: "상위 플랜으로 변경하면 언제 적용되나요?",
    answer:
      "현재 플랜보다 plan_rank가 높은 플랜으로 변경하면 업그레이드로 분류됩니다. 기존 구독의 남은 이용 가치를 정산해 차액 결제가 필요한 경우 즉시 결제 후 새 플랜이 적용되는 구조입니다.",
  },
  {
    category: "payment",
    question: "낮은 플랜으로 변경하면 바로 다운그레이드되나요?",
    answer:
      "아니요. 현재 플랜보다 plan_rank가 낮은 플랜은 다운그레이드 예약으로 처리됩니다. 현재 이용 기간은 종료일까지 유지되고, 기간 종료 시점에 예약된 플랜으로 변경됩니다.",
  },
  {
    category: "payment",
    question: "결제 내역과 영수증은 어디서 확인하나요?",
    answer:
      "설정 화면의 플랜 영역에서 현재 이용 중인 요금제와 결제 내역을 확인할 수 있습니다. 결제 응답에 영수증 URL이 있는 경우 영수증 확인 버튼을 통해 상세 내역을 볼 수 있습니다. 환불은 고객센터의 결제 및 환불 문의로 접수해 주세요.",
  },
  {
    category: "security",
    question: "업로드한 원본 파일은 얼마나 보관되나요?",
    answer:
      "약관과 화면 안내 기준으로 업로드 원본 파일은 기본적으로 최대 12시간 보관 후 자동 삭제하는 정책을 따릅니다. 미완료 업로드나 만료 대상 파일도 정리 대상이 될 수 있습니다.",
  },
  {
    category: "security",
    question: "처리 결과물은 언제까지 받을 수 있나요?",
    answer:
      "결과 파일 보관 기간은 플랜 정책에 따라 달라집니다. 플랜에는 결과 보관 일수, 원본 자동 삭제 시간, 메타데이터 보존 일수 같은 정책 값이 포함되어 있으며, 관리자는 정책 화면에서 활성 플랜의 값을 관리할 수 있습니다.",
  },
  {
    category: "security",
    question: "AI 학습 데이터 활용 동의는 필수인가요?",
    answer:
      "아니요. AI 학습 데이터 활용 동의는 선택 사항입니다. 동의하지 않아도 핵심 기능은 이용할 수 있으며, 동의 상태는 설정 화면에서 관리할 수 있습니다.",
  },
  {
    category: "security",
    question: "결제 정보나 Billing Key는 어떻게 다루나요?",
    answer:
      "자동결제용 Billing Key는 원문을 화면, API 응답, 로그에 노출하지 않는 것을 원칙으로 합니다. 서버에는 암호화된 값과 추적용 해시, 마스킹 카드 정보처럼 필요한 정보만 저장하는 구조입니다.",
  },
  {
    category: "security",
    question: "워터마크는 왜 적용되나요?",
    answer:
      "처리 결과물의 악용이나 위변조 의심 신고가 들어왔을 때 처리 이력을 추적하기 위해 워터마크와 관련 메타데이터를 사용할 수 있습니다. 워터마크 정책은 플랜별 설정과 결과물 처리 정책에 따라 달라질 수 있습니다.",
  },
  {
    category: "sns",
    question: "SNS 계정을 Garim에 직접 연결할 수 있나요?",
    answer:
      "현재 MVP에서는 SNS 계정 자동 연결 기능을 제공하지 않습니다. SNS 연결 화면에서도 외부 SNS 로그인, 권한 요청, 토큰 저장을 수행하지 않으며 파일 업로드 방식으로 먼저 개인정보 탐지 흐름을 제공합니다.",
  },
  {
    category: "sns",
    question: "Instagram 게시물을 자동으로 가져오거나 다시 올려주나요?",
    answer:
      "아니요. 현재는 Instagram 게시물을 자동 수집하거나 재게시하지 않습니다. 사용자가 직접 파일을 내려받아 Garim에 업로드하고, 처리 완료 후 결과 파일을 직접 사용하는 방식입니다.",
  },
  {
    category: "sns",
    question: "SNS 연동은 언제 제공되나요?",
    answer:
      "SNS 연동은 백엔드 인증 정책, 권한 범위, 토큰 보관 방식, 외부 플랫폼 정책 검토가 끝난 뒤 별도 기능으로 제공할 예정입니다. 현재는 업로드 기반 분석과 처리 기능을 우선 제공합니다.",
  },
  {
    category: "spec",
    question: "지원하는 파일 형식은 무엇인가요?",
    answer:
      "업로드 화면 기준으로 MP4, AVI, MOV, MKV 영상 파일과 JPG, PNG, JPEG, WEBP 이미지 파일을 선택할 수 있습니다. 정책 설정에서는 허용 확장자 목록을 관리할 수 있습니다.",
  },
  {
    category: "spec",
    question: "파일 크기 제한은 어떻게 되나요?",
    answer:
      "업로드 화면 기준 Free는 50MB, Pro는 500MB, Studio는 2GB로 안내됩니다. 실제 제한값은 현재 사용자의 플랜 정보와 서버 정책에 따라 적용됩니다.",
  },
  {
    category: "spec",
    question: "업로드는 어떤 방식으로 진행되나요?",
    answer:
      "파일은 5MB 단위 chunk로 나뉘어 업로드됩니다. 전송 실패 chunk는 최대 3회 자동 재시도하고, 모든 chunk가 전송되면 서버에서 병합한 뒤 분석 작업을 생성합니다.",
  },
  {
    category: "spec",
    question: "권장 영상 길이와 해상도는 어떻게 되나요?",
    answer:
      "업로드 화면은 최대 영상 길이 30분, 권장 해상도 1080p로 안내하고 있습니다. 파일이 크거나 길수록 업로드와 분석 시간이 늘어날 수 있습니다.",
  },
];

function getCategoryCount(categoryId) {
  if (categoryId === "all") return FAQ_ITEMS.length;
  return FAQ_ITEMS.filter((item) => item.category === categoryId).length;
}

export default function Faq() {
  useDocumentTitle("도움말·FAQ · Garim");
  const [activeCategory, setActiveCategory] = useState("all");
  const [query, setQuery] = useState("");

  const activeCategoryLabel =
    CATEGORIES.find((category) => category.id === activeCategory)?.label || "전체";

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return FAQ_ITEMS.filter((item) => {
      const matchesCategory =
        activeCategory === "all" || item.category === activeCategory;
      const matchesQuery =
        !normalizedQuery ||
        `${item.question} ${item.answer}`.toLowerCase().includes(normalizedQuery);
      return matchesCategory && matchesQuery;
    });
  }, [activeCategory, query]);

  return (
    <GarimPage bodyClass="page-public" screenLabel="03 FAQ">
      <div className="faq-page">
        <div className="faq-head">
          <h1>무엇을 도와드릴까요?</h1>
          <div className="search-bar">
            <span className="material-icons">search</span>
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="키워드 검색 — 예: 한국어 음성, 환불, 자동 삭제"
            />
          </div>
        </div>
        <div className="faq-grid">
          <aside className="cat-side">
            <h3>카테고리</h3>
            {CATEGORIES.map((category) => (
              <a
                href="#"
                key={category.id}
                className={activeCategory === category.id ? "active" : ""}
                onClick={(event) => {
                  event.preventDefault();
                  setActiveCategory(category.id);
                }}
              >
                <span className="material-icons faq-ico">{category.icon}</span>
                {category.label}
                <span className="count">{getCategoryCount(category.id)}</span>
              </a>
            ))}
          </aside>
          <main className="faq-list">
            <h2>{activeCategory === "all" ? "전체 FAQ" : `${activeCategoryLabel} FAQ`}</h2>
            <div className="crumb">
              {query.trim()
                ? `"${query.trim()}" 검색 결과 ${filteredItems.length}건`
                : `${activeCategoryLabel} 질문 ${filteredItems.length}건`}
            </div>

            {filteredItems.length > 0 ? (
              filteredItems.map((item, index) => (
                <details className="accordion" open={index === 0} key={item.question}>
                  <summary>
                    <h4>{item.question}</h4>
                    <span className="material-icons">expand_more</span>
                  </summary>
                  <div className="answer">{item.answer}</div>
                </details>
              ))
            ) : (
              <div className="faq-empty">
                검색 결과가 없습니다. 다른 키워드로 다시 검색해 주세요.
              </div>
            )}

            <div className="contact-card">
              <div className="faq-contact-ico">
                <span className="material-icons">support_agent</span>
              </div>
              <div className="faq-contact-body">
                <h3>원하는 답을 못 찾으셨나요?</h3>
                <p>
                  고객센터 및 신고 접수 페이지에서 버그, 오탐지, 결제, 환불 문의를 남겨주세요.
                </p>
              </div>
              <Link to="/support" className="mui-btn mui-btn--contained">
                문의하기
              </Link>
            </div>
          </main>
        </div>
      </div>
    </GarimPage>
  );
}
