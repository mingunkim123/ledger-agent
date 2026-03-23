import { sqliteTable, text, integer, index, uniqueIndex } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const users = sqliteTable("users", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  username: text("username").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  isActive: integer("is_active", { mode: "boolean" }).notNull().default(true),
  createdAt: text("created_at").notNull().default(sql`(datetime('now'))`),
});

export const transactions = sqliteTable(
  "transactions",
  {
    txId: text("tx_id").primaryKey(),
    userId: text("user_id").notNull(),
    occurredDate: text("occurred_date").notNull(),
    type: text("type", { enum: ["expense", "income"] }).notNull(),
    amount: integer("amount").notNull(),
    currency: text("currency").notNull().default("KRW"),
    category: text("category").notNull(),
    subcategory: text("subcategory").notNull().default("기타"),
    merchant: text("merchant"),
    memo: text("memo"),
    sourceText: text("source_text"),
    createdAt: text("created_at").notNull().default(sql`(datetime('now'))`),
    updatedAt: text("updated_at").notNull().default(sql`(datetime('now'))`),
  },
  (table) => [
    index("idx_tx_user_date").on(table.userId, table.occurredDate),
    index("idx_tx_user_cat").on(table.userId, table.category),
    index("idx_tx_user_subcat").on(table.userId, table.subcategory),
  ]
);

export const idempotencyKeys = sqliteTable(
  "idempotency_keys",
  {
    userId: text("user_id").notNull(),
    idemKey: text("idem_key").notNull(),
    txId: text("tx_id")
      .notNull()
      .references(() => transactions.txId, { onDelete: "cascade" }),
    createdAt: text("created_at").notNull().default(sql`(datetime('now'))`),
  },
  (table) => [
    uniqueIndex("pk_idempotency").on(table.userId, table.idemKey),
  ]
);

export const auditLogs = sqliteTable(
  "audit_logs",
  {
    eventId: text("event_id").primaryKey(),
    userId: text("user_id").notNull(),
    action: text("action", {
      enum: ["create", "update", "delete", "undo"],
    }).notNull(),
    txId: text("tx_id").references(() => transactions.txId, {
      onDelete: "set null",
    }),
    beforeSnapshot: text("before_snapshot"),
    afterSnapshot: text("after_snapshot"),
    createdAt: text("created_at").notNull().default(sql`(datetime('now'))`),
  },
  (table) => [
    index("idx_audit_user_created").on(table.userId, table.createdAt),
  ]
);