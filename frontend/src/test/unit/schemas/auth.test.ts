import { describe, it, expect } from "vitest";
import {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from "@/schemas/auth";

describe("RegisterRequest", () => {
  const validPayload = {
    username: "john",
    email: "john.doe@gmail.com",
    full_name: "John Doe",
    role: "admin",
    password: "secret123",
    confirm_password: "secret123",
  };

  it("passes with valid data", async () => {
    await expect(RegisterRequest.validate(validPayload)).resolves.toMatchObject(
      validPayload,
    );
  });

  it("fails when username is empty", async () => {
    await expect(
      RegisterRequest.validate({ ...validPayload, username: "" }),
    ).rejects.toThrow();
  });

  it("fails when email is empty", async () => {
    await expect(
      RegisterRequest.validate({ ...validPayload, email: "" }),
    ).rejects.toThrow();
  });

  it("fails when full_name is empty", async () => {
    await expect(
      RegisterRequest.validate({ ...validPayload, full_name: "" }),
    ).rejects.toThrow();
  });

  it("fails when password is empty", async () => {
    await expect(
      RegisterRequest.validate({ ...validPayload, password: "" }),
    ).rejects.toThrow();
  });

  it("fails when passwords do not match", async () => {
    await expect(
      RegisterRequest.validate({
        ...validPayload,
        confirm_password: "SECRET123",
      }),
    ).rejects.toThrow();
  });
});

describe("RegisterResponse", () => {
  const validResponse = {
    message:
      "Signup request successfully completed! You will shortly recieve a verification request in your email address...",
    email_task_id: crypto.randomUUID(),
  };

  it("passes with valid data", async () => {
    await expect(
      RegisterResponse.validate(validResponse),
    ).resolves.toMatchObject(validResponse);
  });

  it("fails with unexpected message", async () => {
    await expect(
      RegisterResponse.validate({
        ...validResponse,
        message: "User successfully registered!",
      }),
    ).rejects.toThrow();
  });

  it("fails with invalid task_id", async () => {
    await expect(
      RegisterRequest.validate({
        ...validResponse,
        email_task_id: "not-a-uuid",
      }),
    ).rejects.toThrow();
  });
});

describe("LoginRequest", () => {
  it("passes with valid data", async () => {
    await expect(
      LoginRequest.validate({ username: "john", password: "secret" }),
    ).resolves.toMatchObject({ username: "john", password: "secret" });
  });

  it("fails when username is empty", async () => {
    await expect(
      LoginRequest.validate({ username: "", password: "secret" }),
    ).rejects.toThrow();
  });

  it("fails when password is empty", async () => {
    await expect(
      LoginRequest.validate({ username: "john", password: "" }),
    ).rejects.toThrow();
  });

  it("fails when username is missing", async () => {
    await expect(
      LoginRequest.validate({ password: "secret" }),
    ).rejects.toThrow();
  });

  it("fails when password is missing", async () => {
    await expect(LoginRequest.validate({ username: "john" })).rejects.toThrow();
  });
});

describe("LoginResponse", () => {
  const validResponse = {
    user_id: 1,
    username: "john",
    email: "john@example.com",
    role: "user",
    created_at: "2024-01-01T00:00:00Z",
  };

  it("passes with valid data", async () => {
    await expect(LoginResponse.validate(validResponse)).resolves.toMatchObject(
      validResponse,
    );
  });

  it("fails when user_id is missing", async () => {
    const { user_id: _, ...rest } = validResponse;
    await expect(LoginResponse.validate(rest)).rejects.toThrow();
  });

  it("fails when email is missing", async () => {
    const { email: _, ...rest } = validResponse;
    await expect(LoginResponse.validate(rest)).rejects.toThrow();
  });

  it("fails when role is missing", async () => {
    const { role: _, ...rest } = validResponse;
    await expect(LoginResponse.validate(rest)).rejects.toThrow();
  });

  it("fails when role is incorrect", async () => {
    await expect(
      LoginResponse.validate({ ...validResponse, role: "invalid-role" }),
    ).rejects.toThrow();
  });

  it("fails when created_at is missing", async () => {
    const { created_at: _, ...rest } = validResponse;
    await expect(LoginResponse.validate(rest)).rejects.toThrow();
  });

  it("strips unknown fields", async () => {
    const result = await LoginResponse.validate(
      { ...validResponse, extra: "field" },
      { stripUnknown: true },
    );
    expect(result).not.toHaveProperty("extra");
  });
});
