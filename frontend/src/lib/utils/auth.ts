import { LogoutResponse } from "@/schemas/auth";
import { toast } from "react-toastify";
import { NavigateFunction } from "react-router-dom";
import HttpRequest from "@/lib/api/http-request";

export async function logoutUser(navigate: NavigateFunction): Promise<void> {
  localStorage.clear();

  const request = new HttpRequest(`${API_URL}/auth/logout`);
  const [response, error] = await request.send(LogoutResponse);

  if (response) {
    toast.success(response.message);
    navigate("/login");
  }

  if (error) {
    toast.error(error);
  }
}
