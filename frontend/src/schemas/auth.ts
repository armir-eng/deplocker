import * as z from "zod";

export const UsernameAvailabilty = z.object({
  available: z.boolean(),
});

export const RegisterRequest = z
  .object({
    username: z
      .string()
      .min(2, "Username must be at least 2 characters.")
      .optional(),
    email: z.email("Please, provide a valid email address."),
    full_name: z.string().min(1),
    role: z.enum(["admin", "user"]).optional(),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters long.")
      .optional(),
    confirm_password: z.string().optional(),
  })
  .refine((values) => values.confirm_password === values.password, {
    error: "Passwords do not match!",
    path: ["confirm_password"],
  });

export const RegisterResponse = z.object({
  message: z.literal(
    "Signup request successfully completed! You will shortly recieve a verification request in your email address...",
  ),
  email_task_id: z.uuid("Invalid UUID format"),
});

export const LoginRequest = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

export const LoginResponse = z.object({
  user_id: z.number().int(),
  email: z.email(),
  role: z.enum(["admin", "user"]),
  created_at: z.string().min(1),
});

export const LogoutResponse = z.object({
  message: z.literal("User successfully logged out!"),
});
