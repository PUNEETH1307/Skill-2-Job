ALTER TABLE student_profile
  ADD COLUMN backlogs_count INT NOT NULL DEFAULT 0;

CREATE TABLE placement_drive (
  id INT AUTO_INCREMENT PRIMARY KEY,
  company_id INT NOT NULL,
  job_role_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  job_description TEXT NULL,
  package_lpa FLOAT NULL,
  location VARCHAR(255) NULL,
  eligibility_criteria TEXT NULL,
  minimum_cgpa FLOAT NOT NULL DEFAULT 0,
  allowed_graduation_years_json TEXT NULL,
  no_backlogs_required TINYINT(1) NOT NULL DEFAULT 0,
  registration_deadline DATETIME(6) NULL,
  drive_date DATE NOT NULL,
  drive_time VARCHAR(30) NULL,
  attendance_code VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
  FOREIGN KEY (job_role_id) REFERENCES job_role(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE drive_shortlist (
  id INT AUTO_INCREMENT PRIMARY KEY,
  drive_id INT NOT NULL,
  profile_id INT NOT NULL,
  compatibility_score FLOAT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'shortlisted',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_drive_shortlist_profile (drive_id, profile_id),
  FOREIGN KEY (drive_id) REFERENCES placement_drive(id) ON DELETE CASCADE,
  FOREIGN KEY (profile_id) REFERENCES student_profile(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE drive_registration
  ADD COLUMN drive_id INT NULL,
  ADD COLUMN attended TINYINT(1) NOT NULL DEFAULT 0,
  ADD KEY idx_drive_registration_profile (profile_id),
  DROP INDEX uq_drive_registration_profile_role,
  ADD UNIQUE KEY uq_drive_registration_profile_drive (profile_id, drive_id),
  ADD CONSTRAINT fk_drive_registration_drive FOREIGN KEY (drive_id) REFERENCES placement_drive(id) ON DELETE CASCADE;