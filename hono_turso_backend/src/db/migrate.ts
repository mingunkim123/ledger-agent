import { migrate } from "drizzle-orm/libsql/migrator";
import { db } from "./client.js";

async function main() {
  console.log("마이그레이션 시작...");
  await migrate(db, { migrationsFolder: "drizzle/migrations" });
  console.log("마이그레이션 완료!");
  process.exit(0);
}

main().catch((err) => {
  console.error("마이그레이션 실패:", err);
  process.exit(1);
});