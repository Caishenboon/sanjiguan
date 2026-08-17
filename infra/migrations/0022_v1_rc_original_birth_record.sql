-- V1 RC: preserve the complete, user-confirmed original birth record.
-- Existing encrypted columns remain for indexed mechanical access and replay compatibility.
BEGIN;

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS original_birth_record_ciphertext bytea;

COMMENT ON COLUMN profiles.original_birth_record_ciphertext IS
  'Encrypted canonical OriginalBirthRecord as submitted by the user; NULL only for legacy rows.';

COMMIT;
