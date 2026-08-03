import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import React from "react";

const mockCall = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/api-client", () => ({
  default: class MockAPIClient {
    call = mockCall;
  },
}));

import useCheckAuthSession from "@/lib/hooks/auth-session";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter>{children}</MemoryRouter>
);

describe("useCheckAuthSession", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns null before the API responds", () => {
    mockCall.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useCheckAuthSession(), { wrapper });
    expect(result.current).toBeNull();
  });

  it("returns true when session is active", async () => {
    mockCall.mockResolvedValue([
      { user_id: 1, username: "john", role: "user", created_at: "2024-01-01" },
      null,
    ]);
    const { result } = renderHook(() => useCheckAuthSession(), { wrapper });
    await waitFor(() => expect(result.current).toBe(true));
  });

  it("returns false when session check fails", async () => {
    mockCall.mockResolvedValue([null, "Unauthorized"]);
    const { result } = renderHook(() => useCheckAuthSession(), { wrapper });
    await waitFor(() => expect(result.current).toBe(false));
  });
});
