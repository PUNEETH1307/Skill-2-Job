-- ============================================================================
-- Skill2Job: AI-Driven Placement Coordination and Skill Mapping System
-- Complete MySQL Database Schema
-- ============================================================================
-- Normalization: 3NF (Third Normal Form)
-- Engine: InnoDB (supports foreign keys and transactions)
-- Charset: utf8mb4 (full Unicode support)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `skill2job` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `skill2job`;

-- ============================================================================
-- TABLE 1: users (unified user table with role-based access)
-- Stores students, admins, and placement officers in a single table
-- Role column differentiates: 'student', 'admin', 'placement_officer'
-- ============================================================================

CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `phone` VARCHAR(20) DEFAULT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('student', 'admin', 'placement_officer') NOT NULL DEFAULT 'student',
  `status` ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX `idx_users_email` (`email`),
  INDEX `idx_users_role` (`role`),
  INDEX `idx_users_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 2: students (student profile - academic and career details)
-- One-to-one relationship with users (where role='student')
-- ============================================================================

CREATE TABLE IF NOT EXISTS `students` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL UNIQUE,
  `institution` VARCHAR(255) DEFAULT NULL,
  `degree` VARCHAR(100) DEFAULT NULL,
  `branch` VARCHAR(100) DEFAULT NULL,
  `cgpa` FLOAT DEFAULT NULL,
  `graduation_year` INT DEFAULT NULL,
  `skills_json` TEXT DEFAULT NULL COMMENT 'JSON array of skill names',
  `skill_vector_json` TEXT DEFAULT NULL COMMENT 'Binary vector for ML matching',
  `dream_job` VARCHAR(150) DEFAULT NULL COMMENT 'Target job role for AI resume',
  `expected_lpa` FLOAT DEFAULT NULL COMMENT 'Expected salary in Lakhs Per Annum',
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX `idx_students_user_id` (`user_id`),
  INDEX `idx_students_graduation_year` (`graduation_year`),
  INDEX `idx_students_cgpa` (`cgpa`),
  CONSTRAINT `fk_students_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 3: admins (admin-specific profile data)
-- One-to-one relationship with users (where role='admin')
-- ============================================================================

CREATE TABLE IF NOT EXISTS `admins` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL UNIQUE,
  `department` VARCHAR(150) DEFAULT NULL,
  `designation` VARCHAR(150) DEFAULT NULL,
  `permissions_json` TEXT DEFAULT NULL COMMENT 'JSON object of admin permissions',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT `fk_admins_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 4: placement_officers (placement officer profile data)
-- One-to-one relationship with users (where role='placement_officer')
-- ============================================================================

CREATE TABLE IF NOT EXISTS `placement_officers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL UNIQUE,
  `department` VARCHAR(150) DEFAULT NULL,
  `designation` VARCHAR(150) DEFAULT NULL,
  `assigned_batch_year` INT DEFAULT NULL COMMENT 'Batch year this officer manages',
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT `fk_officers_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 5: skills (skill taxonomy - canonical skill definitions)
-- Master table of all recognized skills with categories and synonyms
-- ============================================================================

CREATE TABLE IF NOT EXISTS `skills` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `canonical_name` VARCHAR(150) NOT NULL UNIQUE,
  `category` VARCHAR(100) DEFAULT NULL COMMENT 'e.g., Programming Languages, Frameworks, Databases',
  `synonyms_json` TEXT DEFAULT NULL COMMENT 'JSON array of alternate names',
  `description` TEXT DEFAULT NULL,
  `is_deprecated` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_skills_canonical` (`canonical_name`),
  INDEX `idx_skills_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 6: student_skills (many-to-many: students <-> skills)
-- Junction table linking students to their skills with proficiency
-- ============================================================================

CREATE TABLE IF NOT EXISTS `student_skills` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `skill_id` INT NOT NULL,
  `proficiency_level` ENUM('beginner', 'intermediate', 'advanced', 'expert') NOT NULL DEFAULT 'intermediate',
  `years_experience` FLOAT DEFAULT NULL,
  `is_verified` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Verified via assessment or certificate',
  `added_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY `uk_student_skill` (`student_id`, `skill_id`),
  INDEX `idx_student_skills_student` (`student_id`),
  INDEX `idx_student_skills_skill` (`skill_id`),
  CONSTRAINT `fk_student_skills_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_student_skills_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 7: companies (companies offering placements)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `companies` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL,
  `industry` VARCHAR(150) DEFAULT NULL,
  `location` VARCHAR(255) DEFAULT NULL,
  `website` VARCHAR(500) DEFAULT NULL,
  `contact_email` VARCHAR(255) DEFAULT NULL,
  `contact_phone` VARCHAR(20) DEFAULT NULL,
  `description` TEXT DEFAULT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_companies_industry` (`industry`),
  INDEX `idx_companies_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 8: job_roles (job positions offered by companies)
-- Each job role belongs to one company and has skill requirements
-- ============================================================================

CREATE TABLE IF NOT EXISTS `job_roles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `company_id` INT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `required_skills_json` TEXT DEFAULT NULL COMMENT 'JSON array of required skill names',
  `job_vector_json` TEXT DEFAULT NULL COMMENT 'Binary vector for cosine similarity matching',
  `min_cgpa` FLOAT DEFAULT 0.0 COMMENT 'Minimum CGPA threshold',
  `experience_level` ENUM('entry', 'mid', 'senior') DEFAULT 'entry',
  `salary_lpa_min` FLOAT DEFAULT NULL,
  `salary_lpa_max` FLOAT DEFAULT NULL,
  `vacancies` INT DEFAULT 1,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `deadline` DATE DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_job_roles_company` (`company_id`),
  INDEX `idx_job_roles_active` (`is_active`),
  INDEX `idx_job_roles_deadline` (`deadline`),
  CONSTRAINT `fk_job_roles_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 9: applications (student applications to job roles)
-- Tracks application status and compatibility scores
-- ============================================================================

CREATE TABLE IF NOT EXISTS `applications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `job_role_id` INT NOT NULL,
  `compatibility_score` FLOAT DEFAULT NULL COMMENT 'AI-computed match score (0-100)',
  `status` ENUM('pending', 'shortlisted', 'interviewed', 'selected', 'rejected', 'withdrawn') NOT NULL DEFAULT 'pending',
  `applied_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `notes` TEXT DEFAULT NULL COMMENT 'Officer/admin notes on application',
  UNIQUE KEY `uk_student_job_application` (`student_id`, `job_role_id`),
  INDEX `idx_applications_student` (`student_id`),
  INDEX `idx_applications_job` (`job_role_id`),
  INDEX `idx_applications_status` (`status`),
  CONSTRAINT `fk_applications_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_applications_job` FOREIGN KEY (`job_role_id`) REFERENCES `job_roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 10: resumes (generated and uploaded resumes)
-- Tracks both AI-generated and manually uploaded resumes
-- ============================================================================

CREATE TABLE IF NOT EXISTS `resumes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `type` ENUM('ai_generated', 'uploaded') NOT NULL DEFAULT 'ai_generated',
  `original_filename` VARCHAR(255) DEFAULT NULL,
  `stored_filename` VARCHAR(255) NOT NULL,
  `content_type` VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
  `file_size_bytes` INT DEFAULT NULL,
  `dream_job_used` VARCHAR(150) DEFAULT NULL COMMENT 'Dream job at time of generation',
  `ai_content_json` TEXT DEFAULT NULL COMMENT 'JSON snapshot of AI-generated content',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Current active resume',
  `generated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_resumes_student` (`student_id`),
  INDEX `idx_resumes_type` (`type`),
  CONSTRAINT `fk_resumes_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 11: recommendations (AI job recommendations for students)
-- Stores computed job recommendations with scores and reasoning
-- ============================================================================

CREATE TABLE IF NOT EXISTS `recommendations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `job_role_id` INT NOT NULL,
  `compatibility_score` FLOAT NOT NULL COMMENT 'Cosine similarity score (0-100)',
  `rank_position` INT NOT NULL COMMENT 'Rank among all recommendations for this student',
  `matched_skills_json` TEXT DEFAULT NULL COMMENT 'JSON array of matched skills',
  `reasoning` TEXT DEFAULT NULL COMMENT 'AI explanation of why this job matches',
  `is_viewed` TINYINT(1) NOT NULL DEFAULT 0,
  `is_applied` TINYINT(1) NOT NULL DEFAULT 0,
  `computed_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY `uk_student_job_recommendation` (`student_id`, `job_role_id`),
  INDEX `idx_recommendations_student` (`student_id`),
  INDEX `idx_recommendations_score` (`compatibility_score`),
  CONSTRAINT `fk_recommendations_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_recommendations_job` FOREIGN KEY (`job_role_id`) REFERENCES `job_roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 12: courses (course recommendations for skill gaps)
-- Maps skills to learning resources
-- ============================================================================

CREATE TABLE IF NOT EXISTS `courses` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `skill_id` INT NOT NULL,
  `course_name` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(150) DEFAULT NULL COMMENT 'e.g., Coursera, Udemy, edX',
  `url` VARCHAR(500) DEFAULT NULL,
  `difficulty_level` ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
  `duration_hours` INT DEFAULT NULL,
  `rating` FLOAT DEFAULT NULL COMMENT 'Course rating (0-5)',
  `is_free` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_courses_skill` (`skill_id`),
  INDEX `idx_courses_provider` (`provider`),
  CONSTRAINT `fk_courses_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 13: skill_gaps (identified skill gaps per student per job)
-- Stores AI-computed skill deficiencies for targeted learning
-- ============================================================================

CREATE TABLE IF NOT EXISTS `skill_gaps` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `job_role_id` INT NOT NULL,
  `skill_id` INT NOT NULL,
  `deficit_score` FLOAT NOT NULL COMMENT 'Gap severity (0.0-1.0)',
  `priority` ENUM('high', 'medium', 'low') NOT NULL DEFAULT 'medium',
  `status` ENUM('identified', 'in_progress', 'resolved') NOT NULL DEFAULT 'identified',
  `recommended_course_id` INT DEFAULT NULL,
  `identified_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `resolved_at` DATETIME(6) DEFAULT NULL,
  UNIQUE KEY `uk_student_job_skill_gap` (`student_id`, `job_role_id`, `skill_id`),
  INDEX `idx_skill_gaps_student` (`student_id`),
  INDEX `idx_skill_gaps_job` (`job_role_id`),
  INDEX `idx_skill_gaps_status` (`status`),
  CONSTRAINT `fk_skill_gaps_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_skill_gaps_job` FOREIGN KEY (`job_role_id`) REFERENCES `job_roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_skill_gaps_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_skill_gaps_course` FOREIGN KEY (`recommended_course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- TABLE 14: analytics (placement analytics and event tracking)
-- Stores aggregated metrics and placement events for dashboards
-- ============================================================================

CREATE TABLE IF NOT EXISTS `analytics` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `event_type` ENUM('placement', 'application', 'shortlist', 'skill_analysis', 'resume_generated', 'login') NOT NULL,
  `user_id` INT DEFAULT NULL,
  `student_id` INT DEFAULT NULL,
  `job_role_id` INT DEFAULT NULL,
  `company_id` INT DEFAULT NULL,
  `metadata_json` TEXT DEFAULT NULL COMMENT 'JSON object with event-specific data',
  `department` VARCHAR(150) DEFAULT NULL,
  `batch_year` INT DEFAULT NULL,
  `event_date` DATE NOT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_analytics_event_type` (`event_type`),
  INDEX `idx_analytics_user` (`user_id`),
  INDEX `idx_analytics_date` (`event_date`),
  INDEX `idx_analytics_department` (`department`),
  INDEX `idx_analytics_batch` (`batch_year`),
  CONSTRAINT `fk_analytics_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_analytics_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_analytics_job` FOREIGN KEY (`job_role_id`) REFERENCES `job_roles` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_analytics_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- ADDITIONAL SUPPORTING TABLES
-- ============================================================================

-- Projects linked to student profiles
CREATE TABLE IF NOT EXISTS `projects` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `technologies` VARCHAR(500) DEFAULT NULL,
  `github_url` VARCHAR(500) DEFAULT NULL,
  `start_date` DATE DEFAULT NULL,
  `end_date` DATE DEFAULT NULL,
  INDEX `idx_projects_student` (`student_id`),
  CONSTRAINT `fk_projects_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Certifications linked to student profiles
CREATE TABLE IF NOT EXISTS `certifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `issuer` VARCHAR(255) DEFAULT NULL,
  `issue_date` DATE DEFAULT NULL,
  `expiry_date` DATE DEFAULT NULL,
  `credential_url` VARCHAR(500) DEFAULT NULL,
  INDEX `idx_certifications_student` (`student_id`),
  CONSTRAINT `fk_certifications_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Password reset tokens
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `token_hash` VARCHAR(128) NOT NULL UNIQUE,
  `expires_at` DATETIME(6) NOT NULL,
  `used` TINYINT(1) NOT NULL DEFAULT 0,
  INDEX `idx_reset_token_hash` (`token_hash`),
  CONSTRAINT `fk_reset_token_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Uncategorized skills flagged for admin review
CREATE TABLE IF NOT EXISTS `uncategorized_skills` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `term` VARCHAR(255) NOT NULL,
  `occurrence_count` INT NOT NULL DEFAULT 1,
  `reviewed` TINYINT(1) NOT NULL DEFAULT 0,
  `flagged_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_uncategorized_term` (`term`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Placement records (confirmed placements)
CREATE TABLE IF NOT EXISTS `placement_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `job_role_id` INT NOT NULL,
  `company_id` INT NOT NULL,
  `placement_date` DATE DEFAULT NULL,
  `package_lpa` FLOAT DEFAULT NULL COMMENT 'Offered package in LPA',
  `department` VARCHAR(150) DEFAULT NULL,
  `offer_letter_filename` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX `idx_placements_date` (`placement_date`),
  INDEX `idx_placements_dept` (`department`),
  INDEX `idx_placements_student` (`student_id`),
  CONSTRAINT `fk_placements_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_placements_job` FOREIGN KEY (`job_role_id`) REFERENCES `job_roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_placements_company` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================================
-- ER DIAGRAM EXPLANATION
-- ============================================================================
--
-- RELATIONSHIPS:
--
-- users (1) ──── (1) students          [One user has one student profile]
-- users (1) ──── (1) admins            [One user has one admin profile]
-- users (1) ──── (1) placement_officers [One user has one officer profile]
--
-- students (1) ──── (M) student_skills  [Student has many skills]
-- skills (1) ──── (M) student_skills    [Skill belongs to many students]
-- (Many-to-Many via junction table student_skills)
--
-- companies (1) ──── (M) job_roles      [Company offers many job roles]
-- students (1) ──── (M) applications    [Student applies to many jobs]
-- job_roles (1) ──── (M) applications   [Job role has many applications]
--
-- students (1) ──── (M) resumes         [Student has many resumes]
-- students (1) ──── (M) recommendations [Student gets many recommendations]
-- job_roles (1) ──── (M) recommendations [Job appears in many recommendations]
--
-- skills (1) ──── (M) courses           [Skill has many course recommendations]
-- students (1) ──── (M) skill_gaps      [Student has many skill gaps]
-- job_roles (1) ──── (M) skill_gaps     [Job role reveals many gaps]
-- skills (1) ──── (M) skill_gaps        [Skill appears in many gaps]
-- courses (1) ──── (M) skill_gaps       [Course recommended for many gaps]
--
-- students (1) ──── (M) projects        [Student has many projects]
-- students (1) ──── (M) certifications  [Student has many certifications]
-- students (1) ──── (M) placement_records [Student can have placements]
--
-- analytics references users, students, job_roles, companies (all optional FKs)
--
-- NORMALIZATION (3NF):
-- - No repeating groups (1NF): All columns are atomic
-- - No partial dependencies (2NF): All non-key columns depend on full PK
-- - No transitive dependencies (3NF): No non-key column depends on another non-key
-- - skills_json/skill_vector_json are denormalized for ML performance
--   (the normalized version is in student_skills junction table)
--
-- ER DIAGRAM (Mermaid):
--
-- ```mermaid
-- erDiagram
--     USERS ||--o| STUDENTS : "has profile"
--     USERS ||--o| ADMINS : "has profile"
--     USERS ||--o| PLACEMENT_OFFICERS : "has profile"
--
--     STUDENTS ||--o{ STUDENT_SKILLS : "possesses"
--     SKILLS ||--o{ STUDENT_SKILLS : "held by"
--
--     COMPANIES ||--o{ JOB_ROLES : "offers"
--     STUDENTS ||--o{ APPLICATIONS : "applies"
--     JOB_ROLES ||--o{ APPLICATIONS : "receives"
--
--     STUDENTS ||--o{ RESUMES : "generates"
--     STUDENTS ||--o{ RECOMMENDATIONS : "receives"
--     JOB_ROLES ||--o{ RECOMMENDATIONS : "recommended for"
--
--     SKILLS ||--o{ COURSES : "taught by"
--     STUDENTS ||--o{ SKILL_GAPS : "has gaps"
--     JOB_ROLES ||--o{ SKILL_GAPS : "requires"
--     SKILLS ||--o{ SKILL_GAPS : "missing"
--     COURSES ||--o{ SKILL_GAPS : "resolves"
--
--     STUDENTS ||--o{ PROJECTS : "built"
--     STUDENTS ||--o{ CERTIFICATIONS : "earned"
--     STUDENTS ||--o{ PLACEMENT_RECORDS : "placed at"
--     JOB_ROLES ||--o{ PLACEMENT_RECORDS : "filled by"
--     COMPANIES ||--o{ PLACEMENT_RECORDS : "hired"
--
--     USERS ||--o{ ANALYTICS : "triggers"
-- ```
--
-- ============================================================================
