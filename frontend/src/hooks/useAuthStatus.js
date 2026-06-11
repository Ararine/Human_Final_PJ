import { useEffect, useState } from "react";

import { getCurrentUser } from "../utils/api";

// [한글 주석] 로그인 여부를 나타내는 비-HttpOnly 쿠키의 존재를 확인하는 헬퍼 함수입니다.
function checkLoggedInCookie() {
  if (typeof document === "undefined") return false;
  return document.cookie.split(";").some((item) => item.trim().startsWith("logged_in=yes"));
}

// [한글 주석] 기존 로그인 여부만 간단히 노출하는 훅입니다.
export function useAuthStatus() {
  return useAuthUser().isAuthenticated;
}

// [한글 주석] 로그인 여부, 사용자 정보 및 로딩 여부를 반환하는 인증 상태 관리 훅입니다.
export function useAuthUser() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // [한글 주석] 초기 로딩 여부를 관리하는 상태 변수입니다.

  useEffect(() => {
    let isMounted = true;

    // [한글 주석] 브라우저 쿠키에 logged_in=yes 가 없다면 비로그인 상태이므로
    // API 호출을 생략하고 즉시 비로그인 상태로 판정하여 불필요한 401 갱신 오버헤드를 방지합니다.
    if (!checkLoggedInCookie()) {
      if (isMounted) {
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
      }
      return;
    }

    // [한글 주석] 로그인 쿠키 플래그가 있는 경우에만 /auth/me 엔드포인트(getCurrentUser)를 호출해 세션을 검증합니다.
    getCurrentUser()
      .then((status) => {
        if (isMounted) {
          setIsAuthenticated(Boolean(status.authenticated));
          setUser(status.user ?? null);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setIsAuthenticated(false);
          setUser(null);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { isAuthenticated, user, loading };
}


