import { createMiddleware } from "hono/factory";
import { jwtVerify, SignJWT } from "jose";
import { env } from "../lib/env.js";
import type { Variables } from "../types/index.js";

const secret = new TextEncoder().encode(env.JWT_SECRET);

export const authMiddleware = createMiddleware<{ Variables: Variables }>(
  async (c, next) => {
    const header = c.req.header("Authorization");
    if (!header || !header.startsWith("Bearer ")) {
      return c.json(
        { success: false, code: "not_authenticated", message: "인증이 필요합니다", data: null },
        401
      );
    }

    const token = header.slice(7);
    try {
      const { payload } = await jwtVerify(token, secret);
      c.set("user", {
        id: payload.user_id as number,
        username: payload.username as string,
      });
      await next();
    } catch {
      return c.json(
        { success: false, code: "token_invalid", message: "유효하지 않은 토큰입니다", data: null },
        401
      );
    }
  }
);

export async function generateAccessToken(userId: number, username: string): Promise<string> {
  return new SignJWT({ user_id: userId, username })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime(`${env.JWT_ACCESS_EXPIRES_IN}s`)
    .setIssuedAt()
    .sign(secret);
}

export async function generateRefreshToken(userId: number, username: string): Promise<string> {
  return new SignJWT({ user_id: userId, username, type: "refresh" })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime(`${env.JWT_REFRESH_EXPIRES_IN}s`)
    .setIssuedAt()
    .sign(secret);
}

export async function verifyRefreshToken(token: string) {
  const { payload } = await jwtVerify(token, secret);
  if (payload.type !== "refresh") throw new Error("Not a refresh token");
  return { userId: payload.user_id as number, username: payload.username as string };
}