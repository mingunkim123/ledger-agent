import "dotenv/config";

function required(key: string): string {
  const value = process.env[key];
  if (!value) throw new Error(`환경 변수 ${key}가 설정되지 않았습니다`);
  return value;
}

function optional(key: string, fallback: string = ""): string {
  return process.env[key] || fallback;
}

export const env = {
  TURSO_DATABASE_URL: required("TURSO_DATABASE_URL"),
  TURSO_AUTH_TOKEN: optional("TURSO_AUTH_TOKEN"),

  JWT_SECRET: required("JWT_SECRET"),
  JWT_ACCESS_EXPIRES_IN: Number(optional("JWT_ACCESS_EXPIRES_IN", "1800")),
  JWT_REFRESH_EXPIRES_IN: Number(optional("JWT_REFRESH_EXPIRES_IN", "604800")),

  REDIS_URL: optional("REDIS_URL", "redis://localhost:6379/0"),

  LLM_PROVIDER: optional("LLM_PROVIDER", "groq"),
  GROQ_API_KEY: optional("GROQ_API_KEY"),
  GEMINI_API_KEY: optional("GEMINI_API_KEY"),
  GROK_API_KEY: optional("GROK_API_KEY"),
  OLLAMA_BASE_URL: optional("OLLAMA_BASE_URL", "http://localhost:11434"),
  OLLAMA_MODEL: optional("OLLAMA_MODEL", "llama3"),

  PORT: Number(optional("PORT", "8001")),
} as const;