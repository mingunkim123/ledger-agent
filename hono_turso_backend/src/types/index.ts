import type { Context } from "hono";

export type AuthUser = {
  id: number;
  username: string;
};

export type Variables = {
  user: AuthUser;
};

export type AppContext = Context<{ Variables: Variables }>;

export type ApiResponse<T = unknown> = {
  success: boolean;
  code: string;
  message: string;
  data: T | null;
};