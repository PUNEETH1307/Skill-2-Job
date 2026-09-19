-- Dream Job targets and missed-registration enforcement
ALTER TABLE student_profile
  ADD COLUMN missed_drive_blocks INT NOT NULL DEFAULT 0;

CREATE TABLE dream_job (
  id INT AUTO_INCREMENT PRIMARY KEY,
  profile_id INT NOT NULL,
  job_role_id INT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT uq_dream_job_profile_role UNIQUE (profile_id, job_role_id),
  CONSTRAINT fk_dream_job_profile FOREIGN KEY (profile_id) REFERENCES student_profile(id) ON DELETE CASCADE,
  CONSTRAINT fk_dream_job_role FOREIGN KEY (job_role_id) REFERENCES job_role(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE drive_registration (
  id INT AUTO_INCREMENT PRIMARY KEY,
  profile_id INT NOT NULL,
  job_role_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'registered',
  registered_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  marked_at DATETIME(6) NULL,
  CONSTRAINT uq_drive_registration_profile_role UNIQUE (profile_id, job_role_id),
  CONSTRAINT fk_drive_registration_profile FOREIGN KEY (profile_id) REFERENCES student_profile(id) ON DELETE CASCADE,
  CONSTRAINT fk_drive_registration_role FOREIGN KEY (job_role_id) REFERENCES job_role(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
