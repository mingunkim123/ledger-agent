CREATE TABLE `audit_logs` (
	`event_id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`action` text NOT NULL,
	`tx_id` text,
	`before_snapshot` text,
	`after_snapshot` text,
	`created_at` text DEFAULT (datetime('now')) NOT NULL,
	FOREIGN KEY (`tx_id`) REFERENCES `transactions`(`tx_id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE INDEX `idx_audit_user_created` ON `audit_logs` (`user_id`,`created_at`);--> statement-breakpoint
CREATE TABLE `idempotency_keys` (
	`user_id` text NOT NULL,
	`idem_key` text NOT NULL,
	`tx_id` text NOT NULL,
	`created_at` text DEFAULT (datetime('now')) NOT NULL,
	FOREIGN KEY (`tx_id`) REFERENCES `transactions`(`tx_id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `pk_idempotency` ON `idempotency_keys` (`user_id`,`idem_key`);--> statement-breakpoint
CREATE TABLE `transactions` (
	`tx_id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`occurred_date` text NOT NULL,
	`type` text NOT NULL,
	`amount` integer NOT NULL,
	`currency` text DEFAULT 'KRW' NOT NULL,
	`category` text NOT NULL,
	`subcategory` text DEFAULT '기타' NOT NULL,
	`merchant` text,
	`memo` text,
	`source_text` text,
	`created_at` text DEFAULT (datetime('now')) NOT NULL,
	`updated_at` text DEFAULT (datetime('now')) NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_tx_user_date` ON `transactions` (`user_id`,`occurred_date`);--> statement-breakpoint
CREATE INDEX `idx_tx_user_cat` ON `transactions` (`user_id`,`category`);--> statement-breakpoint
CREATE INDEX `idx_tx_user_subcat` ON `transactions` (`user_id`,`subcategory`);--> statement-breakpoint
CREATE TABLE `users` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`username` text NOT NULL,
	`password_hash` text NOT NULL,
	`is_active` integer DEFAULT true NOT NULL,
	`created_at` text DEFAULT (datetime('now')) NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `users_username_unique` ON `users` (`username`);