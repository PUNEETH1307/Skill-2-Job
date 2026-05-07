# Requirements Document

## Introduction

This feature enhances the Skill2Job Placement System by replacing the existing static navigation-only dashboards with feature-rich, data-driven landing pages for each of the three user roles: Student, Placement Coordinator (placement_officer), and Admin. Each dashboard serves as the primary entry point after login, presenting role-relevant summary data, key metrics, quick-action shortcuts, and contextual navigation. The dashboards consume existing backend API endpoints and the new dashboard-specific summary endpoints to aggregate and display data without requiring users to navigate to individual pages for basic status checks.

## Glossary

- **Student_Dashboard**: The landing page displayed to authenticated users with the "student" role, showing profile completion status, skill summary, job match highlights, and quick actions
- **Coordinator_Dashboard**: The landing page displayed to authenticated users with the "placement_officer" role, showing placement activity overview, company and job role counts, recent shortlisting activity, and quick actions
- **Admin_Dashboard**: The landing page displayed to authenticated users with the "admin" role, showing system-wide statistics, user account summaries, taxonomy health indicators, and administrative quick actions
- **Dashboard_API**: The backend REST endpoint(s) that aggregate and return role-specific summary data for dashboard rendering
- **Summary_Card**: A UI component on a dashboard that displays a single metric (label and value) such as "Total Students: 150"
- **Quick_Action**: A prominent UI element (button or link) on a dashboard that navigates the user to a frequently used feature page
- **Profile_Completeness**: A percentage value (0 to 100) representing how many of the required student profile fields have been filled in
- **System**: The Skill2Job Placement System as a whole
- **Student_Interface**: The React frontend pages accessible to students
- **Admin_Interface**: The React frontend pages accessible to placement officers and administrators

## Requirements

### Requirement 1: Student Dashboard Summary Data

**User Story:** As a Student, I want to see a summary of my profile status, skills, and job matches on my dashboard, so that I can quickly understand my placement readiness without navigating to individual pages.

#### Acceptance Criteria

1. WHEN a Student opens the Student_Dashboard, THE Dashboard_API SHALL return the Student's Profile_Completeness as a percentage value between 0 and 100 within 3 seconds.
2. WHEN a Student opens the Student_Dashboard, THE Dashboard_API SHALL return the total count of skills extracted from the Student's profile.
3. WHEN a Student opens the Student_Dashboard, THE Dashboard_API SHALL return the count of active job roles that match the Student's eligibility criteria.
4. WHEN a Student opens the Student_Dashboard, THE Dashboard_API SHALL return the top 3 job recommendations sorted by Compatibility_Score in descending order, each including job title, company name, and Compatibility_Score as a percentage.
5. WHEN a Student opens the Student_Dashboard and the Student has no profile data saved, THE Student_Interface SHALL display Profile_Completeness as 0% and show a prompt to complete the profile.
6. WHEN a Student opens the Student_Dashboard and no active job roles exist, THE Student_Interface SHALL display the matched jobs count as 0 and show a message indicating no job roles are currently available.

### Requirement 2: Student Dashboard Quick Actions

**User Story:** As a Student, I want quick-action shortcuts on my dashboard, so that I can navigate to key features (profile, skills, jobs, resume) with a single click.

#### Acceptance Criteria

1. THE Student_Dashboard SHALL display Quick_Action links to the Profile page, Skill Analysis page, Job Recommendations page, and Resume page.
2. WHEN a Student clicks a Quick_Action link, THE Student_Interface SHALL navigate the Student to the corresponding feature page.
3. WHEN a Student has not completed the profile (Profile_Completeness below 100%), THE Student_Dashboard SHALL visually highlight the Profile Quick_Action to encourage profile completion.

### Requirement 3: Student Dashboard Skill Breakdown Display

**User Story:** As a Student, I want to see a categorized breakdown of my skills on the dashboard, so that I can understand my skill distribution at a glance.

#### Acceptance Criteria

1. WHEN a Student opens the Student_Dashboard and the Student has skills in the profile, THE Dashboard_API SHALL return the skill count grouped by category (e.g., Programming Languages, Frameworks, Databases, Tools).
2. WHEN a Student opens the Student_Dashboard and the Student has skills in the profile, THE Student_Interface SHALL display the categorized skill breakdown as a visual summary (e.g., list with category names and counts).
3. WHEN a Student opens the Student_Dashboard and the Student has no skills in the profile, THE Student_Interface SHALL display a message indicating no skills have been added and prompt the Student to update the profile.

### Requirement 4: Coordinator Dashboard Placement Overview

**User Story:** As a Placement_Officer, I want to see aggregate placement statistics on my dashboard, so that I can monitor placement progress without navigating to the analytics page.

#### Acceptance Criteria

1. WHEN a Placement_Officer opens the Coordinator_Dashboard, THE Dashboard_API SHALL return the total number of registered students, the number of placed students, the total number of companies, and the overall placement percentage within 3 seconds.
2. WHEN a Placement_Officer opens the Coordinator_Dashboard, THE Dashboard_API SHALL return the count of active job roles and the count of total shortlisted candidates.
3. WHEN a Placement_Officer opens the Coordinator_Dashboard, THE Admin_Interface SHALL display each statistic as a Summary_Card with a label and value.

### Requirement 5: Coordinator Dashboard Recent Activity

**User Story:** As a Placement_Officer, I want to see recent shortlisting and placement activity on my dashboard, so that I can stay informed about the latest placement actions.

#### Acceptance Criteria

1. WHEN a Placement_Officer opens the Coordinator_Dashboard, THE Dashboard_API SHALL return the 5 most recent shortlist records, each including the student name, job title, company name, compatibility score, and shortlisted date, sorted by shortlisted date in descending order.
2. WHEN a Placement_Officer opens the Coordinator_Dashboard and no shortlist records exist, THE Admin_Interface SHALL display a message indicating no recent shortlisting activity.
3. WHEN a Placement_Officer opens the Coordinator_Dashboard, THE Dashboard_API SHALL return the top 5 most in-demand skills across active job roles with their occurrence counts.

### Requirement 6: Coordinator Dashboard Quick Actions

**User Story:** As a Placement_Officer, I want quick-action shortcuts on my dashboard, so that I can navigate to company management, job roles, shortlisting, analytics, and course management with a single click.

#### Acceptance Criteria

1. THE Coordinator_Dashboard SHALL display Quick_Action links to the Companies page, Job Roles page, Candidate Shortlisting page, Placement Analytics page, and Course Recommendations page.
2. WHEN a Placement_Officer clicks a Quick_Action link, THE Admin_Interface SHALL navigate the Placement_Officer to the corresponding feature page.

### Requirement 7: Admin Dashboard System Overview

**User Story:** As an Admin, I want to see system-wide statistics on my dashboard, so that I can monitor the health and usage of the placement system.

#### Acceptance Criteria

1. WHEN an Admin opens the Admin_Dashboard, THE Dashboard_API SHALL return the total number of user accounts grouped by role (student, placement_officer, admin) and by status (active, inactive) within 3 seconds.
2. WHEN an Admin opens the Admin_Dashboard, THE Dashboard_API SHALL return the total number of skills in the taxonomy, the count of deprecated skills, and the count of uncategorized skills pending review.
3. WHEN an Admin opens the Admin_Dashboard, THE Admin_Interface SHALL display each statistic as a Summary_Card with a label and value.
4. WHEN an Admin opens the Admin_Dashboard, THE Dashboard_API SHALL return the placement overview statistics (total students, placed students, total companies, placement percentage).

### Requirement 8: Admin Dashboard Quick Actions

**User Story:** As an Admin, I want quick-action shortcuts on my dashboard, so that I can navigate to user management, skill taxonomy, and all placement officer features with a single click.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display Quick_Action links to the User Management page, Skill Taxonomy page, Companies page, Job Roles page, Candidate Shortlisting page, Placement Analytics page, and Course Recommendations page.
2. WHEN an Admin clicks a Quick_Action link, THE Admin_Interface SHALL navigate the Admin to the corresponding feature page.
3. THE Admin_Dashboard SHALL visually distinguish Admin-only Quick_Actions (User Management, Skill Taxonomy) from shared Placement_Officer Quick_Actions.

### Requirement 9: Dashboard API Endpoint

**User Story:** As a developer, I want a single dashboard summary API endpoint per role, so that the frontend can fetch all dashboard data in one request instead of multiple calls.

#### Acceptance Criteria

1. WHEN a Student sends a GET request to the student dashboard endpoint, THE Dashboard_API SHALL return a JSON response containing profile completeness, skill count, skill breakdown by category, matched job count, and top 3 job recommendations.
2. WHEN a Placement_Officer sends a GET request to the coordinator dashboard endpoint, THE Dashboard_API SHALL return a JSON response containing placement overview statistics, active job count, shortlisted candidate count, recent shortlist records, and top in-demand skills.
3. WHEN an Admin sends a GET request to the admin dashboard endpoint, THE Dashboard_API SHALL return a JSON response containing user counts by role and status, taxonomy health statistics, and placement overview statistics.
4. IF an unauthenticated user sends a request to any dashboard endpoint, THEN THE Dashboard_API SHALL return a 401 authentication error.
5. IF a user sends a request to a dashboard endpoint for a different role (e.g., a Student requesting the admin dashboard), THEN THE Dashboard_API SHALL return a 403 authorization error.

### Requirement 10: Dashboard Loading and Error States

**User Story:** As a user of the system, I want clear feedback while the dashboard loads and when errors occur, so that I understand the system state at all times.

#### Acceptance Criteria

1. WHILE the dashboard data is being fetched from the Dashboard_API, THE System SHALL display a loading indicator on the dashboard page.
2. IF the Dashboard_API returns an error response, THEN THE System SHALL display a user-friendly error message on the dashboard page and provide a retry option.
3. WHEN a user clicks the retry option after a dashboard loading error, THE System SHALL re-fetch the dashboard data from the Dashboard_API.

### Requirement 11: Dashboard Data Serialization Consistency

**User Story:** As a developer, I want to verify that dashboard summary data can be reliably serialized and deserialized, so that no data is lost between the backend aggregation and frontend rendering.

#### Acceptance Criteria

1. FOR ALL valid student dashboard responses, serializing the response to JSON and deserializing the JSON back SHALL produce an equivalent data structure (round-trip property).
2. FOR ALL valid coordinator dashboard responses, the placement overview statistics SHALL be consistent with the values returned by the existing analytics endpoint for the same data set (metamorphic property: dashboard overview matches analytics overview).
3. FOR ALL valid admin dashboard responses, the sum of user counts by role SHALL equal the total number of user records in the database (invariant property).
