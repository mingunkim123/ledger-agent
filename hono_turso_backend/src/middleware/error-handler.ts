import type { Context } from "hono";
import { HTTPException } from "hono/http-exception";

export class AppError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string
  ) {
    super(message);
  }
}

export class NotFoundError extends AppError {
  constructor(message = "리소스를 찾을 수 없습니다") {
    super(404, "not_found", message);
  }
}

export class ValidationError extends AppError {
  constructor(message = "입력값이 올바르지 않습니다") {
    super(400, "validation_error", message);
  }
}

export class UndoTokenExpiredError extends AppError {
  constructor() {
    super(400, "undo_token_expired", "취소 토큰이 만료되었습니다");
  }
}

export class TransactionNotFoundError extends AppError {
  constructor() {
    super(404, "transaction_not_found", "거래를 찾을 수 없습니다");
  }
}

export class LLMQuotaExceededError extends AppError {
  constructor() {
    super(429, "llm_quota_exceeded", "LLM API 할당량을 초과했습니다");
  }
}

export function errorHandler(err: Error, c: Context) {
  if (err instanceof AppError) {
    return c.json(
      { success: false, code: err.code, message: err.message, data: null },
      err.statusCode as any
    );
  }

  if (err instanceof HTTPException) {
    return c.json(
      { success: false, code: "http_error", message: err.message, data: null },
      err.status
    );
  }

  console.error("Unhandled error:", err);
  return c.json(
    { success: false, code: "internal_error", message: "서버 내부 오류가 발생했습니다", data: null },
    500
  );
}