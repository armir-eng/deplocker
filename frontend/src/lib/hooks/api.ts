import { useEffect, useState } from "react";
import APIClient from "../api/api-client";
import { AnyObjectSchema, InferType } from "yup";
import { toast } from "react-toastify";
import { APICallParams } from "../api/types";

// This hook helps in components that render API-provided data in their default state (on mount).
// It runs on very first component render, and makes sure the data are immediately fetched.
// Then, the result is combined with a dedicated state varibale to store those data.
// It efficiently uses the APIClient interface, exposing only the result of it, and reducing a considerable amount of boilerplate coming from directly instantiating and consuming it.
export default function useAPIOnMount(
  endpointURL: string,
  responseSchema: AnyObjectSchema,
  apiCallParams?: APICallParams,
) {
  const [response, setResponse] = useState<InferType<AnyObjectSchema> | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const callAPI = async () => {
      const apiClient = new APIClient(endpointURL, apiCallParams);
      const [response, error] = await apiClient.call(responseSchema);

      if (response) {
        setResponse(response);
      }

      if (error) {
        setError(error);
        toast.error(error);
      }
    };

    callAPI();
    // Fetches once on mount; the endpoint/schema/params are treated as fixed
    // for the lifetime of the component.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return [response, error];
}
