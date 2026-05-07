# Implementation Plan: Role-Based Dashboards

## Overview

This plan implements data-driven dashboards for three user roles (Student, Coordinator, Admin) by creating a new `DashboardService` on the backend, new dashboard API routes, a shared `SummaryCard` component on the frontend, and rewriting the two existing dashboard pages. All data is derived from existing database models — no schema changes needed.

## Tasks

- [ ] 1. Create the DashboardService with student summary method
  - [x] 1.1 Create `backend/app/services/dashboard_service.py` with the `DashboardService` class
    - Implement `get_student_summary(user_id)` method that returns `profile_completeness`, `skill_count`, `skill_breakdown`, `matched_job_count`, and `top_recommendations`
    - Profile completeness: check 8 fields (institution, degree, branch, cgpa, graduation_year, skills_json, has_projects, has_certifications) on `StudentProfile`, compute `filled / 8 * 100` rounded to int
    - Skill breakdown: parse `skills_json`, use `SkillAnalyzer.categorize_skills()` to group by category, return dict of category→count
    - Matched job count: query active `JobRole` records where student CGPA >= `cgpa_threshold` and `job_vector_json` is not null
    - Top recommendations: call `JobMatchingEngine.get_recommendations(user_id, limit=3)` and return `job_role_id`, `title`, `company_name`, `compatibility_score`
    - Handle missing profile gracefully: return zeroed-out response with `profile_completeness: 0`, empty skill data, zero counts
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 3.1, 9.1_

  - [x] 1.2 Write property test: Profile completeness is bounded (Property 1)
    - **Property 1: Profile completeness is bounded**
    - Use Hypothesis to generate random combinations of filled/empty profile fields
    - Assert `profile_completeness` is always an integer in [0, 100]
    - Location: `backend/tests/property/test_dashboard_properties.py`
    - **Validates: Requirements 1.1**

  - [x] 1.3 Write property test: Skill breakdown consistency (Property 2)
    - **Property 2: Skill breakdown consistency**
    - Use Hypothesis to generate profiles with varying skill lists
    - Assert sum of all category counts in `skill_breakdown` equals `skill_count`
    - Assert each category count matches the actual number of student skills in that category
    - **Validates: Requirements 1.2, 3.1**

  - [x] 1.4 Write property test: Matched job count equals eligible active jobs (Property 3)
    - **Property 3: Matched job count equals eligible active jobs**
    - Use Hypothesis to generate students with varying CGPAs and sets of active job roles with varying thresholds
    - Assert `matched_job_count` equals the count of active jobs where student CGPA >= threshold and job has a valid vector
    - **Validates: Requirements 1.3**

  - [x] 1.5 Write property test: Top recommendations sorted and limited (Property 4)
    - **Property 4: Top recommendations are sorted and limited**
    - Use Hypothesis to generate varying sets of job recommendations
    - Assert `top_recommendations` has at most 3 items and is sorted by `compatibility_score` descending
    - **Validates: Requirements 1.4**

  - [x] 1.6 Write property test: Student dashboard round-trip serialization (Property 10)
    - **Property 10: Student dashboard response round-trip serialization**
    - Use Hypothesis to generate valid student dashboard response dicts
    - Assert JSON serialize → deserialize produces an equivalent data structure
    - **Validates: Requirements 11.1**

- [ ] 2. Extend DashboardService with coordinator and admin summary methods
  - [x] 2.1 Implement `get_coordinator_summary()` in `DashboardService`
    - Compute `placement_overview` by calling `AnalyticsService.get_overview_stats()`
    - Query `active_job_count` from `JobRole` where `is_active=True`
    - Query `shortlisted_count` as total count of `Shortlist` records
    - Query `recent_shortlists`: 5 most recent `Shortlist` records joined with `User`, `JobRole`, `Company`, sorted by `shortlisted_at` descending, returning student_name, job_title, company_name, compatibility_score, shortlisted_at
    - Compute `top_skills_demand`: aggregate `required_skills_json` from active job roles, count occurrences, return top 5 sorted by count descending
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3, 9.2_

  - [x] 2.2 Implement `get_admin_summary()` in `DashboardService`
    - Compute `user_counts.by_role`: count `User` records grouped by `role`
    - Compute `user_counts.by_status`: count `User` records grouped by `status`
    - Compute `user_counts.total`: total count of `User` records
    - Compute `taxonomy_health.total_skills`: count of non-deprecated `SkillTaxonomy` entries
    - Compute `taxonomy_health.deprecated_skills`: count of deprecated `SkillTaxonomy` entries
    - Compute `taxonomy_health.uncategorized_pending`: count of `UncategorizedSkill` where `reviewed=False`
    - Compute `placement_overview` by calling `AnalyticsService.get_overview_stats()`
    - _Requirements: 7.1, 7.2, 7.4, 9.3_

  - [x] 2.3 Write property test: Coordinator counts match database state (Property 5)
    - **Property 5: Coordinator counts match database state**
    - Use Hypothesis to generate varying sets of active/inactive job roles and shortlist records
    - Assert `active_job_count` equals count of `JobRole` with `is_active=True` and `shortlisted_count` equals total `Shortlist` count
    - **Validates: Requirements 4.2**

  - [x] 2.4 Write property test: Recent shortlists sorted and limited (Property 6)
    - **Property 6: Recent shortlists are sorted and limited**
    - Use Hypothesis to generate varying sets of shortlist records with different timestamps
    - Assert `recent_shortlists` has at most 5 items and is sorted by `shortlisted_at` descending
    - **Validates: Requirements 5.1**

  - [x] 2.5 Write property test: Top skills demand sorted and limited (Property 7)
    - **Property 7: Top skills demand is sorted and limited**
    - Use Hypothesis to generate active job roles with varying `required_skills_json`
    - Assert `top_skills_demand` has at most 5 items and is sorted by `count` descending
    - **Validates: Requirements 5.3**

  - [x] 2.6 Write property test: User counts sum invariant (Property 8)
    - **Property 8: User counts correctness with sum invariant**
    - Use Hypothesis to generate varying sets of users with different roles and statuses
    - Assert each `by_role` count matches actual count, each `by_status` count matches actual count, and sum of `by_role` values equals `total`
    - **Validates: Requirements 7.1, 11.3**

  - [x] 2.7 Write property test: Taxonomy health counts (Property 9)
    - **Property 9: Taxonomy health counts correctness**
    - Use Hypothesis to generate varying sets of `SkillTaxonomy` and `UncategorizedSkill` records
    - Assert `total_skills` equals non-deprecated count, `deprecated_skills` equals deprecated count, `uncategorized_pending` equals unreviewed count
    - **Validates: Requirements 7.2**

  - [x] 2.8 Write property test: Dashboard placement overview matches analytics (Property 11)
    - **Property 11: Dashboard placement overview matches analytics service**
    - Use Hypothesis to generate varying database states with placement records
    - Assert coordinator dashboard `placement_overview` values are identical to `AnalyticsService.get_overview_stats()` output
    - **Validates: Requirements 11.2**

- [x] 3. Checkpoint - Verify backend service layer
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Create dashboard API routes
  - [x] 4.1 Create `backend/app/routes/dashboard_routes.py` with Flask Blueprint `dashboard_bp` (prefix `/api/dashboard`)
    - Implement `GET /api/dashboard/student` with `@jwt_required` and `@role_required("student")`, delegate to `DashboardService.get_student_summary(user_id)`, return JSON
    - Implement `GET /api/dashboard/coordinator` with `@jwt_required` and `@role_required("placement_officer")`, delegate to `DashboardService.get_coordinator_summary()`, return JSON
    - Implement `GET /api/dashboard/admin` with `@jwt_required` and `@role_required("admin")`, delegate to `DashboardService.get_admin_summary()`, return JSON
    - Wrap each handler in try/except to return 500 with `INTERNAL_ERROR` on unexpected failures
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 4.2 Register `dashboard_bp` in `backend/app/__init__.py`
    - Import and register the new blueprint in the `create_app` function alongside existing blueprints
    - _Requirements: 9.1_

  - [x] 4.3 Write integration tests for dashboard routes
    - Create `backend/tests/integration/test_dashboard_routes.py`
    - Test authenticated student GET `/api/dashboard/student` → 200 with expected response shape
    - Test authenticated coordinator GET `/api/dashboard/coordinator` → 200 with expected response shape
    - Test authenticated admin GET `/api/dashboard/admin` → 200 with expected response shape
    - Test unauthenticated request → 401
    - Test student requesting coordinator endpoint → 403
    - Test placement_officer requesting admin endpoint → 403
    - _Requirements: 9.4, 9.5_

- [x] 5. Checkpoint - Verify backend routes and integration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Create shared SummaryCard frontend component
  - [x] 6.1 Create `frontend/src/components/SummaryCard.tsx`
    - Implement a reusable card component accepting `label: string`, `value: string | number`, and optional `highlight?: boolean` props
    - Use existing `dash-card` CSS class conventions; add a `dash-summary-card` class for metric display styling
    - When `highlight` is true, apply a visual emphasis style (e.g., `dash-card-highlight` class with accent border)
    - Ensure the component is accessible (proper heading hierarchy, ARIA attributes if needed)
    - _Requirements: 4.3, 7.3_

  - [x] 6.2 Add SummaryCard and dashboard-specific CSS styles to `frontend/src/styles/dashboard.css`
    - Add `.dash-summary-card` styles for metric value display (large font for value, smaller label)
    - Add `.dash-card-highlight` variant with accent/warning border for emphasis
    - Add `.dash-loading` spinner styles for loading state
    - Add `.dash-error` styles for error message with retry button
    - Add `.dash-empty-state` styles for empty data prompts
    - Add `.dash-section` styles for grouping dashboard sections (metrics row, recommendations, quick actions)
    - Add `.dash-recent-table` styles for the coordinator's recent shortlists table
    - _Requirements: 10.1, 10.2_

- [ ] 7. Rewrite Student Dashboard page
  - [x] 7.1 Rewrite `frontend/src/pages/student/Dashboard.tsx`
    - Fetch `GET /api/dashboard/student` on component mount using the `api` axios instance
    - Display loading spinner (`.dash-loading`) while fetching
    - Display error message with retry button on API failure
    - Render SummaryCard components for: profile completeness (highlight if < 100%), skill count, matched jobs count
    - Render skill breakdown as a categorized list with category names and counts
    - Render top 3 job recommendations list showing job title, company name, and compatibility score percentage
    - Render quick-action links to Profile (`/student/profile`), Skill Analysis (`/student/skills`), Job Recommendations (`/student/jobs`), Resume (`/student/resume`)
    - Highlight the Profile quick-action link when `profile_completeness < 100`
    - Show empty-state prompt when profile completeness is 0 (encourage profile completion)
    - Show "no jobs available" message when `matched_job_count` is 0
    - Show "no skills added" message when `skill_count` is 0 with prompt to update profile
    - Keep existing logout button and welcome banner
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 10.1, 10.2, 10.3_

- [ ] 8. Rewrite Admin/Coordinator Dashboard page
  - [x] 8.1 Rewrite `frontend/src/pages/admin/Dashboard.tsx` to serve both coordinator and admin views
    - Check `user.role` from `useAuth()` to determine which endpoint to call (`/dashboard/coordinator` or `/dashboard/admin`)
    - Fetch the appropriate endpoint on component mount using the `api` axios instance
    - Display loading spinner while fetching; display error message with retry button on failure
    - **Coordinator view** (`placement_officer` role):
      - Render SummaryCards for: total students, placed students, total companies, placement percentage, active job count, shortlisted count
      - Render recent shortlists as a table with columns: student name, job title, company name, compatibility score, date
      - Show "no recent activity" message when `recent_shortlists` is empty
      - Render top 5 in-demand skills list with skill name and occurrence count
      - Render quick-action links to: Companies (`/admin/companies`), Job Roles (`/admin/jobs`), Candidate Shortlisting (`/admin/shortlist`), Placement Analytics (`/admin/analytics`), Course Recommendations (`/admin/courses`)
    - **Admin view** (`admin` role):
      - Render SummaryCards for: user counts by role (student, placement_officer, admin), user counts by status (active, inactive), total users
      - Render taxonomy health cards: total skills, deprecated skills, uncategorized pending
      - Render placement overview cards: total students, placed students, total companies, placement percentage
      - Render quick-action links to all coordinator actions PLUS: User Management (`/admin/users`), Skill Taxonomy (`/admin/skills`)
      - Visually distinguish admin-only quick actions (User Management, Skill Taxonomy) using `dash-card-admin` class with `dash-admin-badge`
    - Keep existing logout button and welcome banner
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.1, 6.2, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 10.1, 10.2, 10.3_

- [x] 9. Checkpoint - Verify full frontend and backend integration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Write unit tests for DashboardService
  - [x] 10.1 Create `backend/tests/unit/test_dashboard_service.py`
    - Test `get_student_summary` with no profile → completeness 0%, empty skills, zero job matches
    - Test `get_student_summary` with fully complete profile → completeness 100%
    - Test `get_student_summary` with partial profile → correct percentage
    - Test `get_student_summary` with skills but no active job roles → `matched_job_count` 0
    - Test `get_coordinator_summary` with no shortlists → empty `recent_shortlists` list
    - Test `get_coordinator_summary` with shortlists → correct counts and ordering
    - Test `get_admin_summary` with no users → all counts zero
    - Test `get_admin_summary` with mixed users → correct role/status counts
    - _Requirements: 1.1, 1.5, 1.6, 4.1, 4.2, 5.2, 7.1, 7.2_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate the 11 universal correctness properties defined in the design
- Unit tests validate specific examples and edge cases
- The backend uses Python (Flask/SQLAlchemy) and the frontend uses TypeScript (React)
- Hypothesis is already installed (`hypothesis==6.123.17` in requirements.txt) and configured in `pytest.ini`
- All property tests go in `backend/tests/property/test_dashboard_properties.py`
- No new database models are needed — all data is derived from existing tables
