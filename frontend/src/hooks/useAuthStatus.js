import { useEffect, useState } from "react";

import { getAuthStatus } from "../utils/api";

export function useAuthStatus() {
  return useAuthUser().isAuthenticated;
}

export function useAuthUser() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    let isMounted = true;

    getAuthStatus()
      .then((status) => {
        if (isMounted) {
          setIsAuthenticated(Boolean(status.authenticated));
          setUser(status.user ?? null);
        }
      })
      .catch(() => {
        if (isMounted) {
          setIsAuthenticated(false);
          setUser(null);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { isAuthenticated, user };
}
