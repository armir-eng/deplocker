import { useEffect, useState } from "react";
import HttpRequest from "../api/http-request";
import * as z from "zod";
import { toast } from "react-toastify";
import { APICallParams } from "../api/types";

// This hook helps in components that render API-provided data in their default state (on mount).
// It runs on very first component render, and makes sure the data are immediately fetched.
// Then, the result is combined with a dedicated state varibale to store those data.
// It efficiently uses the HttpRequest interface, exposing only the result of it, and reducing a considerable amount of boilerplate coming from directly instantiating and consuming it.
export default function useAPIOnMount<S extends z.ZodType>(
  endpointURL: string,
  responseSchema: S,
  apiCallParams?: APICallParams,
) {
  const [response, setResponse] = useState<z.infer<S> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const callAPI = async () => {
      const request = new HttpRequest(endpointURL, apiCallParams);
      const [response, error] = await request.send(responseSchema);

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

  return [response, error] as const;
}
