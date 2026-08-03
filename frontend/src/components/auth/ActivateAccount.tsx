import { CheckCircle, Loader2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "../shadcn/button";
import APIClient from "@/lib/api/api-client";
import { useAtom } from "jotai";
import { emailTaskIDAtom } from "@/store/auth.atoms";
import useTaskStatusPolling from "@/lib/hooks/task-polling";
import {
  emailTaskFailureMessage,
  emailTaskSuccessMessage,
} from "../../constants/auth";
import { SuccessReponse } from "@/schemas/shared";

export function ActivateAccount() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");
  const [emailTaskID, setEmailTaskID] = useAtom(emailTaskIDAtom);

  useEffect(() => {
    const confirmAccount = async () => {
      const email = searchParams.get("email");
      const token = searchParams.get("token");

      if (!token) {
        setStatus("error");
        setMessage("Invalid confirmation link");
        return;
      }

      const endpointURL = `${API_URL}/auth/account/confirm?email=${email}&token=${token}`;
      const apiClient = new APIClient(endpointURL);

      const [result, error] = await apiClient.call(SuccessReponse);
      if (result) {
        setStatus("success");
        setMessage("Account was successfully activated!");
      }
      if (error) {
        console.error(error);
        setStatus("error");
        setMessage(
          "Failed to activate the account! The token might be invalid or might have been expired. Please, try again.",
        );
      }
    };

    confirmAccount();
    // Runs once on mount to confirm the account from the URL params.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useTaskStatusPolling(
    emailTaskID,
    setEmailTaskID,
    emailTaskSuccessMessage,
    emailTaskFailureMessage,
  );

  const resendConfirmationEmail = async () => {
    setStatus("loading");
    const email = searchParams.get("email");
    const endpointURL = `${API_URL}/auth/account/confirm/retry?email=${email}`;
    const apiClient = new APIClient(endpointURL);
    const [result, error] = await apiClient.call();

    if (result) {
      setStatus("success");
    }

    if (error) {
      setStatus("error");
    }
  };

  return (
    <div className="flex w-full justify-center items-center mt-4">
      <div className="flex flex-col gap-8">
        {status === "loading" && (
          <div className="flex flex-col items-center">
            <Loader2 className="animate-spin" />
            <p>Confirming your email...</p>
          </div>
        )}

        {status === "success" && (
          <div className="flex flex-col gap-8">
            <CheckCircle className="text-green-500" />
            <p>{message}</p>
            <Button
              className="cursor-pointer"
              onClick={() => navigate("/login")}
            >
              Go to Login Now
            </Button>
          </div>
        )}

        {status === "error" && (
          <div className="flex flex-col gap-4">
            <XCircle className="animate-pulse duration-200 text-red-500" />
            <h2>Account Confirmation Failed</h2>
            <p>{message}</p>
            <a className="cursor-pointer" onClick={resendConfirmationEmail}>
              Resend email
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
