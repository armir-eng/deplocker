import { useEffect } from "react";
import { RESET } from "jotai/utils";
import { toast } from "react-toastify";
import APIClient from "../api/api-client";
import { TaskStatusPollResponse } from "@/schemas/tasks";

export default function useTaskStatusPolling(
  taskID: string | null,
  setTaskID: (
    update: React.SetStateAction<string | null> | typeof RESET,
  ) => void,
  successMessage: string,
  failureMessage: string,
) {
  useEffect(() => {
    if (taskID) {
      const endpointURL = `${API_URL}/tasks/${taskID}`;
      const apiClient = new APIClient(endpointURL);

      const intervalID = setInterval(async () => {
        const [response, error] = await apiClient.call(TaskStatusPollResponse);

        if (response) {
          if (response.status === "SUCCESS") {
            toast.success(successMessage);
            clearInterval(intervalID);
            setTaskID(RESET);
          } else if (response.status === "FAILURE") {
            toast.error(failureMessage);
            clearInterval(intervalID);
            setTaskID(RESET);
          }
        }

        if (error) {
          toast.error(error);
          clearInterval(intervalID);
          setTaskID(RESET);
        }
      }, 1500);

      return () => clearInterval(intervalID);
    }
    // Polling is keyed on taskID only; the setter and messages are stable for a
    // given in-flight task and must not restart the interval when they change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskID]);
}
