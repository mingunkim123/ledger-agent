import { Hono } from "hono";
import { eq } from "drizzle-orm";
import bcrypt from "bcryptjs";
import { db } from "../db/client.js";
import { users } from "../db/schema.js";
import {
  generateAccessToken,
  generateRefreshToken,
  verifyRefreshToken,
} from "../middleware/auth.js";
import { AppError } from "../middleware/error-handler.js";

const accounts = new Hono();

// POST /register/
accounts.post("/register/", async (c) => {
  const body = await c.req.json();
  const { username, password, password2 } = body;

  // 유효성 검증
  if (!username || username.length < 3 || username.length > 30) {
    throw new AppError(400, "validation_error", "username은 3~30자여야 합니다");
  }
  if (!password || password.length < 8) {
    throw new AppError(400, "validation_error", "비밀번호는 8자 이상이어야 합니다");
  }
  if (password !== password2) {
    throw new AppError(400, "validation_error", "비밀번호가 일치하지 않습니다");
  }

  // 중복 확인
  const existing = await db
    .select()
    .from(users)
    .where(eq(users.username, username))
    .limit(1);

  if (existing.length > 0) {
    throw new AppError(409, "username_taken", "이미 사용 중인 username입니다");
  }

  // 생성
  const passwordHash = await bcrypt.hash(password, 10);
  const result = await db
    .insert(users)
    .values({ username, passwordHash })
    .returning({ id: users.id, username: users.username });

  return c.json({
    success: true,
    code: "user_created",
    message: "회원가입이 완료되었습니다",
    data: { id: result[0].id, username: result[0].username },
  }, 201);
});

// POST /login/
accounts.post("/login/", async (c) => {
  const { username, password } = await c.req.json();

  if (!username || !password) {
    throw new AppError(400, "validation_error", "username과 password를 입력하세요");
  }

  const rows = await db
    .select()
    .from(users)
    .where(eq(users.username, username))
    .limit(1);

  if (rows.length === 0) {
    throw new AppError(401, "invalid_credentials", "아이디 또는 비밀번호가 올바르지 않습니다");
  }

  const user = rows[0];
  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    throw new AppError(401, "invalid_credentials", "아이디 또는 비밀번호가 올바르지 않습니다");
  }

  const access = await generateAccessToken(user.id, user.username);
  const refresh = await generateRefreshToken(user.id, user.username);

  return c.json({
    success: true,
    code: "login_success",
    message: "로그인 성공",
    data: { access, refresh },
  });
});

// POST /token/refresh/
accounts.post("/token/refresh/", async (c) => {
  const { refresh } = await c.req.json();

  if (!refresh) {
    throw new AppError(400, "validation_error", "refresh 토큰을 입력하세요");
  }

  try {
    const { userId, username } = await verifyRefreshToken(refresh);
    const access = await generateAccessToken(userId, username);
    return c.json({
      success: true,
      code: "token_refreshed",
      message: "토큰 갱신 성공",
      data: { access },
    });
  } catch {
    throw new AppError(401, "token_invalid", "유효하지 않은 refresh 토큰입니다");
  }
});

export default accounts;