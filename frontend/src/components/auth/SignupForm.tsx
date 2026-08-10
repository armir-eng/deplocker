import { InferType } from "yup";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/shadcn/card";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/shadcn/field";
import { Input } from "@/components/shadcn/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../shadcn/select";
import { useForm, Controller } from "react-hook-form";
import {
  RegisterRequest,
  RegisterResponse,
  UsernameAvailabilty,
} from "@/schemas/auth";
import { yupResolver } from "@hookform/resolvers/yup";
import APIClient from "@/lib/api/api-client";
import { toast } from "react-toastify";
import { useAtom } from "jotai";
import { emailTaskIDAtom } from "@/store/auth.atoms";
import useTaskStatusPolling from "@/lib/hooks/task-polling";
import {
  emailTaskFailureMessage,
  emailTaskSuccessMessage,
} from "../../constants/auth";
import { useEffect, useState } from "react";
import { Button } from "../shadcn/button";
import GoogleIcon from "./GoogleIcon";
import { Eye, EyeOff } from "lucide-react";

export function SignupForm({ ...props }: React.ComponentProps<typeof Card>) {
  const [emailTaskID, setEmailTaskID] = useAtom(emailTaskIDAtom);
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(
    null,
  );
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<InferType<typeof RegisterRequest>>({
    resolver: yupResolver(RegisterRequest),
    defaultValues: {
      username: "",
      email: "",
      full_name: "",
      role: "user",
      password: "",
      confirm_password: "",
    },
  });

  // react-hook-form's watch() cannot be memoized by the React Compiler; this is
  // the documented way to observe a field value.
  // eslint-disable-next-line react-hooks/incompatible-library
  const username = form.watch("username"); // Track the username field value

  useEffect(() => {
    setUsernameAvailable(null); // Remove the availability message before the check request
    if (!username || username.length < 3) return;
    const timer = setTimeout(async () => {
      const apiClient = new APIClient(
        `${API_URL}/auth/check-username?username=${username}`,
      );
      const [result, error] = await apiClient.call(UsernameAvailabilty);
      if (result) {
        setUsernameAvailable(result.available);
      }

      if (error) {
        toast.error(error);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [username]);

  useTaskStatusPolling(
    emailTaskID,
    setEmailTaskID,
    emailTaskSuccessMessage,
    emailTaskFailureMessage,
  );

  const onToggglePasswordVisibility = () => {
    setShowPassword((prevState) => !prevState);
  };

  const onSubmit = async (data: InferType<typeof RegisterRequest>) => {
    const endpointURL = `${API_URL}/auth/register`;

    // Field is not expected in the payload to the signup (register) endpoint.
    // It is only used for client-side form validation.
    // This way, we delete it from the object.
    delete data["confirm_password"];

    const apiClient = new APIClient(endpointURL, {
      body: data,
    });

    const [response, error] = await apiClient.call(RegisterResponse);
    if (response) {
      toast.info(response.message);
      setEmailTaskID(response.email_task_id);
    }

    if (error) {
      toast.error(error);
    }
  };

  return (
    <div className="flex flex-col items-center m-8 text-base gap-12">
      <div className="flex flex-col items-center">
        <img src="/deplocker.png" width="200px" height="200px"></img>
        <h1 className="text-2xl font-bold">Sign up for Deplocker</h1>
      </div>
      <Card {...props} className="w-full md:w-[35%]">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
          <CardDescription>
            Enter your information below to create your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <FieldGroup>
              <Controller
                name="username"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field>
                    <FieldLabel htmlFor="username">Username</FieldLabel>
                    <Input
                      {...field}
                      id="username"
                      type="text"
                      placeholder="john.doe"
                      required
                    />
                    {fieldState.invalid && (
                      <FieldError
                        errors={[{ message: fieldState.error?.message }]}
                      />
                    )}
                    {username &&
                      username.length > 2 &&
                      usernameAvailable != null &&
                      (usernameAvailable === false ? (
                        <FieldError
                          errors={[
                            { message: `${username} is already taken.` },
                          ]}
                        />
                      ) : (
                        <FieldDescription className="text-green-600">
                          {username} is available ✓
                        </FieldDescription>
                      ))}
                  </Field>
                )}
              />
              <Controller
                name="email"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field>
                    <FieldLabel htmlFor="email">Email</FieldLabel>
                    <Input
                      {...field}
                      id="email"
                      type="email"
                      placeholder="m@example.com"
                      required
                    />
                    {fieldState.invalid ? (
                      <FieldError
                        errors={[{ message: fieldState.error?.message }]}
                      />
                    ) : (
                      <FieldDescription>
                        We&apos;ll use this to contact you. We will not share
                        your email with anyone else.
                      </FieldDescription>
                    )}
                  </Field>
                )}
              />
              <Controller
                name="full_name"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field>
                    <FieldLabel htmlFor="full-name">Full Name</FieldLabel>
                    <Input
                      {...field}
                      id="full-name"
                      type="text"
                      placeholder="John Doe"
                      required
                    />
                    {fieldState.invalid && (
                      <FieldError
                        errors={[{ message: fieldState.error?.message }]}
                      />
                    )}
                  </Field>
                )}
              />
              <Controller
                name="role"
                control={form.control}
                defaultValue="admin"
                render={({ field }) => (
                  <Field>
                    <FieldLabel htmlFor="role">Role</FieldLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="user">User</SelectItem>
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </Field>
                )}
              />
              <Controller
                name="password"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field>
                    <FieldLabel htmlFor="password">Password</FieldLabel>
                    <div className="relative">
                      <Input
                        {...field}
                        id="password"
                        type={showPassword ? "text" : "password"}
                        className="pr-9"
                        required
                      />
                      <button
                        type="button"
                        onClick={onToggglePasswordVisibility}
                        aria-label={
                          showPassword ? "Hide password" : "Show password"
                        }
                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground cursor-pointer"
                      >
                        {showPassword ? (
                          <EyeOff className="size-4" />
                        ) : (
                          <Eye className="size-4" />
                        )}
                      </button>
                    </div>
                    {fieldState.invalid ? (
                      <FieldError
                        errors={[{ message: fieldState.error?.message }]}
                      />
                    ) : (
                      <FieldDescription>
                        Must be at least 8 characters long.
                      </FieldDescription>
                    )}
                  </Field>
                )}
              />
              <Controller
                name="confirm_password"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field>
                    <FieldLabel htmlFor="confirm-password">
                      Confirm Password
                    </FieldLabel>
                    <div className="relative">
                      <Input
                        {...field}
                        id="confirm-password"
                        type={showPassword ? "text" : "password"}
                        className="pr-9"
                        required
                      />
                      <button
                        type="button"
                        onClick={onToggglePasswordVisibility}
                        aria-label={
                          showPassword ? "Hide password" : "Show password"
                        }
                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground cursor-pointer"
                      >
                        {showPassword ? (
                          <EyeOff className="size-4" />
                        ) : (
                          <Eye className="size-4" />
                        )}
                      </button>
                    </div>
                    {fieldState.invalid ? (
                      <FieldError
                        errors={[{ message: fieldState.error?.message }]}
                      />
                    ) : (
                      <FieldDescription>
                        Please confirm your password.
                      </FieldDescription>
                    )}
                  </Field>
                )}
              />
              <FieldGroup>
                <Field>
                  <Button type="submit" className="cursor-pointer">
                    Create Account
                  </Button>
                  <Button
                    variant="outline"
                    type="button"
                    className="cursor-pointer"
                  >
                    <GoogleIcon /> Sign up with Google
                  </Button>
                  <FieldDescription className="px-6 text-center">
                    Already have an account?{" "}
                    <a href="/login" className="hover:text-blue-500!">
                      Sign in
                    </a>
                  </FieldDescription>
                </Field>
              </FieldGroup>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
