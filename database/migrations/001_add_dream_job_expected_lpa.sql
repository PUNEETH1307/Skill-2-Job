-- Migration: Add dream_job and expected_lpa columns to student_profile
-- Date: 2025-01-01
-- Description: Adds fields for AI-powered resume generation feature

ALTER TABLE `student_profile`
  ADD COLUMN `dream_job` VARCHAR(150) DEFAULT NULL,
  ADD COLUMN `expected_lpa` FLOAT DEFAULT NULL;
