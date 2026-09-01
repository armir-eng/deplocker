import { Controller, useForm } from "react-hook-form";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "../shadcn/field";
import { InferType } from "yup";
import { LoginRequest, LoginResponse } from "@/schemas/auth";
import { yupResolver } from "@hookform/resolvers/yup";
import { Input } from "../shadcn/input";
import { Button } from "../shadcn/button";
import GoogleIcon from "@/components/auth/GoogleIcon";
import GithubIcon from "@/components/auth/GithubIcon";
import APIClient from "@/lib/api/api-client";
import { toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import { setOnLocalStorage } from "@/lib/utils";
import useCheckAuthSession from "@/lib/hooks/auth-session";

export default function Login() {
  const navigate = useNavigate();
  const isSessionActive = useCheckAuthSession();

  if (isSessionActive) {
    navigate("/dashboard/projects");
  }
  const form = useForm<InferType<typeof LoginRequest>>({
    resolver: yupResolver(LoginRequest),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit = async (data: InferType<typeof LoginRequest>) => {
    const formData = new FormData();
    formData.append("username", data.username);
    formData.append("password", data.password);

    const apiClient = new APIClient(`${API_URL}/auth/login`, {
      body: formData,
    });
    const [response, error] = await apiClient.call(LoginResponse);

    if (response) {
      setOnLocalStorage("user_id", String(response.user_id));
      setOnLocalStorage("email", response.email);
      navigate("/dashboard/projects");
    }

    if (error) {
      toast.error(error);
    }
  };

  return (
    <div className="flex flex-col h-screen items-center gap-12">
      <div className="flex flex-col items-center">
        <img src="/deplocker.png" width="200px" height="200px"></img>
        <h1 className="text-2xl font-bold">Sign in to Deplocker</h1>
      </div>
      <form
        className="flex flex-col gap-8 w-full px-8 md:w-1/4 md:p-0"
        onSubmit={form.handleSubmit(onSubmit)}
      >
        <FieldGroup>
          <Controller
            name="username"
            control={form.control}
            render={({ field }) => (
              <Field>
                <FieldLabel htmlFor="username" className="text-base">
                  Username
                </FieldLabel>
                <Input
                  {...field}
                  id="username"
                  type="text"
                  placeholder="john or john.doe@gmail.com"
                  required
                />
                <FieldDescription>
                  You can use your username or email to login
                </FieldDescription>
              </Field>
            )}
          />
          <Controller
            name="password"
            control={form.control}
            render={({ field }) => (
              <Field>
                <FieldLabel htmlFor="password">Password</FieldLabel>
                <Input {...field} id="password" type="password" required />
              </Field>
            )}
          />
        </FieldGroup>
        <FieldGroup>
          <Button type="submit" className="cursor-pointer">
            Login
          </Button>
          <div className="flex">
            <div className="grow h-px bg-gray-400 self-center"></div>
            <span className="shrink px-4 text-gray-500">or</span>
            <div className="grow h-px bg-gray-400 self-center"></div>
          </div>
          <Button
            type="button"
            variant="outline"
            className="cursor-pointer"
            onClick={() =>
              window.location.replace(`${API_URL}/auth/google/login`)
            }
          >
            <GoogleIcon /> Sign in with Google
          </Button>
          <Button
            type="button"
            variant="outline"
            className="cursor-pointer"
            onClick={() =>
              window.location.replace(`${API_URL}/auth/github/login`)
            }
          >
            <GithubIcon /> Sign in with Github
          </Button>

          <div className="flex justify-center mb-12">
            <p>
              <>New to Deplocker? </>
              <a href="/register" className="text-blue-500 hover:underline">
                Create an account
              </a>
            </p>
          </div>
        </FieldGroup>
      </form>
    </div>
  );
}
