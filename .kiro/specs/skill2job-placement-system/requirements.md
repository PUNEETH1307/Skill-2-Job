# Requirements Document

## Introduction

Skill2Job is a full-stack web application for AI-driven campus placement coordination and skill mapping. The system automates the placement process by enabling students to register, build profiles, generate professional resumes, and receive AI-powered job recommendations based on skill compatibility. Placement officers can manage companies, shortlist candidates, and analyze placement metrics. The core intelligence relies on NLP-based skill extraction and ML-driven job matching using vector similarity techniques. The system replaces manual, CGPA-centric placement workflows with a data-driven, skill-aware approach.

## Glossary

- **System**: The Skill2Job web application as a whole
- **Student_Interface**: The web-based front-end through which students interact with the system
- **Admin_Interface**: The dashboard used by placement officers and administrators to manage data and monitor placement activities
- **Skill_Analyzer**: The NLP-based engine that extracts, categorizes, and scores skills from student profiles
- **Resume_Generator**: The template-driven module that creates professional resumes in PDF or DOCX format
- **Job_Matching_Engine**: The ML algorithm module that computes compatibility scores between student skill vectors and job requirement vectors
- **Auth_Module**: The authentication and authorization subsystem handling login, registration, and role-based access
- **Database_Server**: The MySQL relational database storing all persistent application data
- **Student**: A registered user who creates a profile, adds skills, generates resumes, and views job recommendations
- **Placement_Officer**: A user who manages companies, sets eligibility criteria, shortlists candidates, and views placement analytics
- **Admin**: A user who manages user accounts, company records, system settings, and overall data
- **Skill_Vector**: A numerical representation of a student's technical skills used for similarity computation
- **Job_Requirement_Vector**: A numerical representation of the skills required for a specific job role
- **Compatibility_Score**: A numerical value (0.0 to 1.0) representing the match between a Skill_Vector and a Job_Requirement_Vector
- **Skill_Gap**: The set of skills present in a Job_Requirement_Vector but absent or weak in a student's Skill_Vector
- **Course_Recommendation**: A suggested online course or learning resource mapped to a specific Skill_Gap
- **Eligibility_Criteria**: A set of conditions (CGPA threshold, required skills, academic status) defined by a Placement_Officer for a job role
- **Placement_Report**: An aggregated analytics view showing placement statistics, success rates, and trends

## Requirements

### Requirement 1: Student Registration

**User Story:** As a Student, I want to create an account with my personal and contact details, so that I can access the placement system and build my profile.

#### Acceptance Criteria

1. WHEN a Student submits a registration form with valid name, email, phone number, and password, THE Auth_Module SHALL create a new Student account and return a confirmation message within 2 seconds.
2. WHEN a Student submits a registration form with an email that already exists in the Database_Server, THE Auth_Module SHALL reject the registration and display an error message indicating the email is already registered.
3. WHEN a Student submits a registration form with an invalid email format, THE Auth_Module SHALL reject the registration and display a validation error specifying the invalid field.
4. WHEN a Student submits a registration form with a password shorter than 8 characters, THE Auth_Module SHALL reject the registration and display a password policy violation message.
5. THE Auth_Module SHALL store Student passwords using a one-way cryptographic hash with a unique salt per account.

### Requirement 2: User Authentication and Session Management

**User Story:** As a registered user (Student, Placement_Officer, or Admin), I want to log in securely and maintain a session, so that I can access features appropriate to my role.

#### Acceptance Criteria

1. WHEN a user submits valid credentials (email and password), THE Auth_Module SHALL authenticate the user and issue a session token within 2 seconds.
2. WHEN a user submits invalid credentials, THE Auth_Module SHALL reject the login attempt and display a generic authentication failure message without revealing whether the email or password was incorrect.
3. WHILE a user session is active, THE Auth_Module SHALL restrict access to resources based on the user's assigned role (Student, Placement_Officer, or Admin).
4. WHEN a user session has been inactive for more than 30 minutes, THE Auth_Module SHALL expire the session and require re-authentication.
5. WHEN a user clicks the logout button, THE Auth_Module SHALL invalidate the session token and redirect the user to the login page.
6. IF a request is made with an expired or invalid session token, THEN THE Auth_Module SHALL return an authentication error and redirect the user to the login page.

### Requirement 3: Student Profile Creation and Management

**User Story:** As a Student, I want to enter and update my academic information, technical skills, certifications, and project details, so that the system can accurately analyze my capabilities.

#### Acceptance Criteria

1. WHEN a Student submits profile information including academic details (institution, degree, branch, CGPA, graduation year), THE Student_Interface SHALL save the profile data to the Database_Server and display a success confirmation.
2. WHEN a Student adds technical skills to the profile, THE Student_Interface SHALL accept each skill as a text entry and store the skill list in the Database_Server.
3. WHEN a Student adds project details (title, description, technologies used), THE Student_Interface SHALL store each project entry linked to the Student's profile in the Database_Server.
4. WHEN a Student updates any profile field, THE Student_Interface SHALL overwrite the previous value in the Database_Server and display the updated profile.
5. THE Student_Interface SHALL validate that required profile fields (name, institution, degree, branch, CGPA) are present before allowing profile submission.
6. WHEN a Student enters a CGPA value outside the range 0.0 to 10.0, THE Student_Interface SHALL reject the input and display a validation error.

### Requirement 4: Automated Resume Generation

**User Story:** As a Student, I want the system to automatically generate a professional resume from my profile data, so that I can use it for placement applications without manual formatting.

#### Acceptance Criteria

1. WHEN a Student requests resume generation, THE Resume_Generator SHALL produce a formatted resume document using the Student's profile data (name, contact, academic details, skills, projects, certifications) within 5 seconds.
2. THE Resume_Generator SHALL output the resume in PDF format.
3. WHEN a Student requests resume generation and the Student's profile is missing required fields (name, institution, degree, skills), THE Resume_Generator SHALL display an error listing the missing fields and refuse to generate the resume.
4. WHEN a Student downloads a generated resume, THE Resume_Generator SHALL serve the file as a downloadable attachment with the filename format "Resume_{StudentName}_{Date}.pdf".
5. THE Resume_Generator SHALL apply a predefined professional template that includes sections for personal information, academic details, technical skills, projects, and certifications.
6. WHEN a Student updates profile data and requests a new resume, THE Resume_Generator SHALL produce a resume reflecting the latest profile data.

### Requirement 5: NLP-Based Skill Extraction and Categorization

**User Story:** As a Student, I want the system to analyze and categorize my technical skills, so that I can understand my skill profile and how it maps to job requirements.

#### Acceptance Criteria

1. WHEN a Student's profile is saved or updated, THE Skill_Analyzer SHALL extract technical skills from the profile text fields (skills list, project descriptions) using NLP techniques within 10 seconds.
2. THE Skill_Analyzer SHALL categorize each extracted skill into one of the predefined categories (Programming Languages, Frameworks, Databases, Tools, Soft Skills, Domain Knowledge).
3. WHEN the Skill_Analyzer processes a Student's profile, THE Skill_Analyzer SHALL generate a Skill_Vector representing the Student's competencies as a numerical array.
4. WHEN the Skill_Analyzer encounters a skill term not present in the system's skill taxonomy, THE Skill_Analyzer SHALL flag the term for Admin review and assign it to an "Uncategorized" category.
5. THE Skill_Analyzer SHALL normalize skill names to canonical forms (e.g., "JS" and "JavaScript" map to "JavaScript") before generating the Skill_Vector.
6. WHEN the Skill_Analyzer completes analysis, THE Student_Interface SHALL display the categorized skill breakdown to the Student.

### Requirement 6: Job Matching and Recommendation

**User Story:** As a Student, I want to receive job role recommendations ranked by compatibility with my skills, so that I can focus my placement efforts on the most suitable opportunities.

#### Acceptance Criteria

1. WHEN a Student requests job recommendations, THE Job_Matching_Engine SHALL compute Compatibility_Scores between the Student's Skill_Vector and all active Job_Requirement_Vectors within 5 seconds.
2. THE Job_Matching_Engine SHALL compute Compatibility_Scores using cosine similarity between the Skill_Vector and each Job_Requirement_Vector.
3. THE Job_Matching_Engine SHALL return job recommendations sorted in descending order of Compatibility_Score.
4. WHEN the Job_Matching_Engine returns recommendations, THE Student_Interface SHALL display each recommendation with the job title, company name, Compatibility_Score (as a percentage), and required skills.
5. WHEN no active job roles exist in the Database_Server, THE Job_Matching_Engine SHALL return an empty result set and THE Student_Interface SHALL display a message indicating no job roles are currently available.
6. THE Job_Matching_Engine SHALL only include job roles where the Student meets the Eligibility_Criteria defined by the Placement_Officer.

### Requirement 7: Skill Gap Identification

**User Story:** As a Student, I want to see which skills I am missing for specific job roles, so that I can work on improving my employability.

#### Acceptance Criteria

1. WHEN a Student views a job recommendation, THE Job_Matching_Engine SHALL compute the Skill_Gap by comparing the Student's Skill_Vector against the Job_Requirement_Vector for that role.
2. THE Job_Matching_Engine SHALL represent each Skill_Gap entry as a skill name and a deficit score (0.0 to 1.0) indicating how far the Student's proficiency is from the required level.
3. WHEN a Skill_Gap is computed, THE Student_Interface SHALL display the missing or weak skills sorted by deficit score in descending order.
4. WHEN a Student's Skill_Vector fully satisfies a Job_Requirement_Vector (no gaps), THE Student_Interface SHALL display a message indicating full skill coverage for that role.

### Requirement 8: Course Recommendation for Skill Gaps

**User Story:** As a Student, I want to receive course suggestions for my skill gaps, so that I can improve my skills and become eligible for more job roles.

#### Acceptance Criteria

1. WHEN a Skill_Gap is identified for a Student, THE System SHALL retrieve Course_Recommendations mapped to each missing or weak skill from the Database_Server.
2. THE System SHALL display each Course_Recommendation with the course name, provider, URL, and the skill it addresses.
3. WHEN no Course_Recommendation exists for a specific skill in the Database_Server, THE Student_Interface SHALL display a message indicating no courses are currently available for that skill.
4. WHEN a Placement_Officer or Admin adds a new Course_Recommendation to the Database_Server, THE System SHALL make the course available for future Skill_Gap recommendations without requiring a system restart.

### Requirement 9: Company and Job Role Management

**User Story:** As a Placement_Officer, I want to add and manage company profiles and job roles with skill requirements, so that the system can match students to relevant opportunities.

#### Acceptance Criteria

1. WHEN a Placement_Officer submits a new company record (company name, industry, location, contact details), THE Admin_Interface SHALL store the record in the Database_Server and display a confirmation.
2. WHEN a Placement_Officer adds a job role to a company (job title, description, required skills, CGPA threshold, eligibility criteria), THE Admin_Interface SHALL store the job role linked to the company in the Database_Server.
3. WHEN a Placement_Officer adds required skills to a job role, THE Skill_Analyzer SHALL generate a Job_Requirement_Vector from the listed skills.
4. WHEN a Placement_Officer updates a company record or job role, THE Admin_Interface SHALL save the changes to the Database_Server and reflect the updates in subsequent job matching operations.
5. WHEN a Placement_Officer deletes a job role, THE Admin_Interface SHALL remove the job role from the Database_Server and exclude the role from future job matching results.
6. WHEN a Placement_Officer submits a company record with missing required fields (company name), THE Admin_Interface SHALL reject the submission and display a validation error.

### Requirement 10: Candidate Shortlisting

**User Story:** As a Placement_Officer, I want to shortlist eligible candidates for specific job roles based on eligibility criteria, so that I can streamline the placement process.

#### Acceptance Criteria

1. WHEN a Placement_Officer requests a candidate shortlist for a job role, THE System SHALL filter Students who meet the Eligibility_Criteria (CGPA threshold, required skills, academic status) and return the filtered list within 5 seconds.
2. THE System SHALL sort the shortlisted candidates by Compatibility_Score in descending order.
3. WHEN a Placement_Officer views the shortlist, THE Admin_Interface SHALL display each candidate's name, CGPA, Compatibility_Score, matched skills, and missing skills.
4. WHEN no Students meet the Eligibility_Criteria for a job role, THE Admin_Interface SHALL display a message indicating no eligible candidates were found.
5. WHEN a Placement_Officer selects candidates from the shortlist, THE Admin_Interface SHALL mark the selected candidates as "Shortlisted" for that job role in the Database_Server.

### Requirement 11: Placement Analytics and Reporting

**User Story:** As a Placement_Officer, I want to view placement statistics and analytics, so that I can track placement progress and identify trends.

#### Acceptance Criteria

1. WHEN a Placement_Officer opens the Placement_Report dashboard, THE Admin_Interface SHALL display aggregate statistics including total students registered, total students placed, total companies, and overall placement percentage.
2. WHEN a Placement_Officer requests a department-wise placement breakdown, THE Admin_Interface SHALL display placement counts and percentages grouped by academic department.
3. WHEN a Placement_Officer requests a company-wise placement breakdown, THE Admin_Interface SHALL display the number of students placed per company.
4. THE Admin_Interface SHALL display a skill demand analysis showing the most frequently required skills across all active job roles.
5. WHEN a Placement_Officer selects a date range filter, THE Admin_Interface SHALL restrict all displayed analytics to placement activities within the specified date range.

### Requirement 12: Admin User and Data Management

**User Story:** As an Admin, I want to manage user accounts, company records, and system settings, so that I can maintain the integrity and operation of the placement system.

#### Acceptance Criteria

1. WHEN an Admin creates a new user account (Student, Placement_Officer, or Admin), THE Admin_Interface SHALL store the account in the Database_Server with the specified role.
2. WHEN an Admin deactivates a user account, THE Auth_Module SHALL prevent the deactivated user from logging in and THE Admin_Interface SHALL display the account status as "Inactive".
3. WHEN an Admin updates system settings (skill taxonomy, course mappings, resume templates), THE System SHALL apply the updated settings to subsequent operations without requiring a system restart.
4. WHEN an Admin views the user management panel, THE Admin_Interface SHALL display a paginated list of all user accounts with name, email, role, and account status.
5. WHEN an Admin searches for a user by name or email, THE Admin_Interface SHALL return matching results within 2 seconds.

### Requirement 13: Skill Taxonomy Management

**User Story:** As an Admin, I want to manage the skill taxonomy (categories, canonical skill names, and synonyms), so that the Skill_Analyzer produces consistent and accurate results.

#### Acceptance Criteria

1. WHEN an Admin adds a new skill to the taxonomy (skill name, category, synonyms), THE Admin_Interface SHALL store the skill entry in the Database_Server.
2. WHEN an Admin adds synonyms for an existing skill, THE Skill_Analyzer SHALL map all listed synonyms to the canonical skill name during skill extraction.
3. WHEN an Admin removes a skill from the taxonomy, THE Admin_Interface SHALL flag the skill as deprecated in the Database_Server and THE Skill_Analyzer SHALL exclude the deprecated skill from future extractions.
4. WHEN an Admin reviews uncategorized skills flagged by the Skill_Analyzer, THE Admin_Interface SHALL display the flagged terms with the frequency of occurrence across Student profiles.

### Requirement 14: Data Validation and Error Handling

**User Story:** As a user of the system, I want clear and informative error messages when something goes wrong, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN a form submission fails server-side validation, THE System SHALL return a response containing the specific field names and validation error descriptions.
2. IF the Database_Server is unreachable, THEN THE System SHALL display a user-friendly error message indicating a temporary service issue and log the database connection error with a timestamp.
3. IF the Skill_Analyzer or Job_Matching_Engine encounters a processing error, THEN THE System SHALL log the error details (module name, input summary, error type, timestamp) and display a user-friendly error message to the requesting user.
4. THE System SHALL validate all user inputs on both the client side (Student_Interface or Admin_Interface) and the server side before processing.

### Requirement 15: Performance and Scalability

**User Story:** As a system stakeholder, I want the system to handle concurrent users and large datasets without degradation, so that the placement process runs smoothly during peak usage.

#### Acceptance Criteria

1. THE System SHALL serve page load requests within 3 seconds under normal load (up to 100 concurrent users).
2. THE Job_Matching_Engine SHALL compute Compatibility_Scores for a Student against up to 500 job roles within 5 seconds.
3. THE System SHALL support at least 100 concurrent authenticated user sessions without response time exceeding 5 seconds for any operation.
4. THE Database_Server SHALL use indexed queries for Student lookups by email, skill searches, and job role filtering to maintain query response times below 1 second.

### Requirement 16: Security and Data Protection

**User Story:** As a system stakeholder, I want user data to be stored and transmitted securely, so that personal information is protected from unauthorized access.

#### Acceptance Criteria

1. THE System SHALL transmit all data between the client and server over HTTPS.
2. THE Auth_Module SHALL enforce role-based access control so that Students cannot access Placement_Officer or Admin endpoints, and Placement_Officers cannot access Admin-only endpoints.
3. THE System SHALL sanitize all user inputs to prevent SQL injection and cross-site scripting (XSS) attacks.
4. THE Database_Server SHALL store personally identifiable information (name, email, phone) in encrypted form at rest.
5. WHEN a user account is deleted, THE System SHALL remove all associated personal data from the Database_Server within 24 hours.

### Requirement 17: Skill Analysis Round-Trip Consistency

**User Story:** As a developer, I want to verify that skill extraction and vector generation are consistent, so that job matching produces reliable results.

#### Acceptance Criteria

1. FOR ALL valid Student profiles, extracting skills and generating a Skill_Vector, then serializing and deserializing the Skill_Vector, SHALL produce a numerically equivalent Skill_Vector (round-trip property).
2. FOR ALL valid job role skill lists, generating a Job_Requirement_Vector, then serializing and deserializing the Job_Requirement_Vector, SHALL produce a numerically equivalent Job_Requirement_Vector (round-trip property).
3. FOR ALL pairs of identical Skill_Vectors, THE Job_Matching_Engine SHALL produce a Compatibility_Score of 1.0 (idempotence of self-matching).
4. FOR ALL Student Skill_Vectors A and Job_Requirement_Vectors B, the Compatibility_Score of A against B SHALL equal the Compatibility_Score of B against A (symmetry property).

### Requirement 18: Resume Data Serialization Consistency

**User Story:** As a developer, I want to ensure that student profile data used for resume generation can be reliably serialized and deserialized, so that no data is lost during the resume generation pipeline.

#### Acceptance Criteria

1. FOR ALL valid Student profile objects, serializing the profile to JSON and deserializing the JSON back to a profile object SHALL produce an equivalent object (round-trip property).
2. FOR ALL valid Student profile objects, generating a resume and extracting structured data sections from the generated resume SHALL contain all skills, projects, and academic details present in the original profile (metamorphic property: no data loss).
