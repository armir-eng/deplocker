import * as yup from "yup";

export const UsernameAvailabilty = yup.object().shape({
  available: yup.boolean().required(),
});

export const RegisterRequest = yup.object().shape({
  username: yup.string().min(2, "Username must be at least 2 characters."),
  email: yup
    .string()
    .email("Please, provide a valid email address.")
    .required(),
  full_name: yup.string().required(),
  role: yup.string().oneOf(["admin", "user"]),
  password: yup.string().min(8, "Password must be at least 8 characters long."),
  confirm_password: yup
    .string()
    .test("passwords-match", "Passwords do not match!", function (value) {
      return value === this.parent.password;
    }),
});

export const RegisterResponse = yup.object().shape({
  message: yup
    .string()
    .oneOf([
      "Signup request successfully completed! You will shortly recieve a verification request in your email address...",
    ])
    .required(),
  email_task_id: yup.string().uuid().required("Invalid UUID format"),
});

export const LoginRequest = yup.object().shape({
  username: yup.string().required(),
  password: yup.string().required(),
});

export const LoginResponse = yup.object().shape({
  user_id: yup.number().integer().required(),
  email: yup.string().email().required(),
  role: yup.string().oneOf(["admin", "user"]).required(),
  created_at: yup.string().required(),
});
