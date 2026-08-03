import { toast } from "react-toastify";
import { resolveEndpointConfig } from "./endpoints-map";
import { networkErrorToasterMessage } from "@/globals";
import { APICallParams, RequestParams } from "./types";
import { AnyObjectSchema, InferType, ValidationError } from "yup";

export type APICallResult<T> = [T | null, string | null];

export default class APIClient {
  endpointURL: string;
  apiCallParams?: APICallParams;

  constructor(endpointURL: string, apiCallParams?: APICallParams) {
    this.endpointURL = endpointURL;
    this.apiCallParams = apiCallParams;
  }

  async call<S extends AnyObjectSchema>(
    schema?: S,
  ): Promise<APICallResult<InferType<S>>> {
    let endpointConfig: RequestParams;

    try {
      endpointConfig = resolveEndpointConfig(this.endpointURL);
    } catch (error) {
      const errorMessage = String(error);
      return [null, errorMessage];
    }

    const init: RequestInit = {
      method: endpointConfig.method,
    };

    if (endpointConfig.headers) {
      init.headers = endpointConfig.headers;
    }
    if (endpointConfig.authenticationRequired) {
      init.credentials = "include";
    }

    const requestPayload = this.apiCallParams?.body;
    if (requestPayload) {
      if (requestPayload instanceof FormData) init.body = requestPayload;
      else if (requestPayload instanceof Object)
        init.body = JSON.stringify(requestPayload);
    }

    try {
      const response = await fetch(this.endpointURL, init);
      const data = await response.json();

      if (!response.ok) {
        const serverErrorDetail = data.detail;
        return [null, serverErrorDetail];
      }

      if (schema) {
        try {
          const validated = await schema.validate(data, { stripUnknown: true });
          return [validated, null];
        } catch (error) {
          if (error instanceof ValidationError) {
            return [null, `Invalid response shape: ${error.message}`];
          }
          throw error; // Rethrow any unexpected issue
        }
      }

      return [data, null];
    } catch (error) {
      let errorMessage: string;

      if (error instanceof TypeError) {
        errorMessage = networkErrorToasterMessage;
      } else if (error instanceof Error) {
        errorMessage = `An unexpected error ocurred: ${error.message}`;
      } else {
        errorMessage = `An unexpected error ocurred: ${error}`;
      }

      toast.error(errorMessage);
      return [null, errorMessage];
    }
  }
}
