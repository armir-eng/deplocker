import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import APIClient from "@/lib/api/api-client";
import { LoginResponse } from "@/schemas/auth";
import {
  clearLocalStorage,
  getFromLocalStorage,
  setOnLocalStorage,
} from "@/lib/utils";

export default function useCheckAuthSession() {
  const [isSessionActive, setIsSessionActive] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkSession = async () => {
      const endpointURL = `${API_URL}/auth/session/check`;
      const apiClient = new APIClient(endpointURL);

      const [response, error] = await apiClient.call(LoginResponse);

      if (response) {
        if (!getFromLocalStorage("user_id")) {
          setOnLocalStorage("user_id", String(response.user_id));
          setOnLocalStorage("email", response.email);
        }
        setIsSessionActive(true);
      }
      if (error) {
        setIsSessionActive(false);
        clearLocalStorage();
        navigate("/login");
      }
    };

    checkSession();
    // `navigate` is stable across renders and intentionally excluded.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSessionActive]);

  return isSessionActive;
}
