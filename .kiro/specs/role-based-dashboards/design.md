# Design Document: Role-Based Dashboards

## Overview

This feature replaces the existing static, navigation-only dashboard pages (`frontend/src/pages/student/Dashboard.tsx` and `frontend/src/pages/admin/Dashboard.tsx`) with data-driven landing pages for each of the three user roles: Student, Placement Coordinator (`placement_officer`), and Admin. Each dashboard fetches aggregated summary data from a new set of backend API endpoints and renders role-relevant metrics, quick-action shortcuts, and contextual navigation.

### Design Decisions

1. **One API endpoint per role**: Each role gets a dedicated `GET /api/dashboard/<role>` endpoint that aggregates all summary data in a single response. This avoids multiple round-trips from the frontend and keeps the dashboard load fast.
2. **New `DashboardService` on the backend**: A new service class composes data from existing services (`AnalyticsService`, `JobMatchingEngine`, `SkillAnalyzer`) and direct model queries. This keeps route handlers thin and logic testable.
3. **Reuse existing frontend patterns**: The dashboards continue using the existing CSS class conventions (`dash-*`), `useAuth` hook, `api` axios instance, and `react-router-dom` `Link` components. New summary card and metric components are added as shared components.
4. **No new database models**: All dashboard data is derived from existing tables. Profile completeness is computed on the fly from `StudentProfile` fields.
5. **Role-based access enforcement**: Each dashboard endpoint uses the existing `@jwt_required` and `@role_required` decorators. The admin endpoint is accessible to `admin` role only; the coordinator endpoint to `placement_officer` (and `admin` via role hierarchy); the student endpoint to `student` only.

## Architecture

```mermaid
graph TD
    subgraph Frontend
        SD[StudentDashboard.tsx]
        CD[CoordinatorDashboard.tsx]
        AD[AdminDashboard.tsx]
        SC[SummaryCard component]
        API_SVC[api.ts axios instance]
    end

    subgraph Backend
        DR[dashboard_routes.py<br>/api/dashboard/*]
        DS[DashboardService]
        AS[AnalyticsService]
        JM[JobMatchingEngine]
        PS[profile_service]
        AUTH[auth_decorator.py<br>@jwt_required @role_required]
    end

    subgraph Database
        U[(User)]
        SP[(StudentProfile)]
        JR[(JobRole)]
        CO[(Company)]
        SL[(Shortlist)]
        ST[(SkillTaxonomy)]
        US[(UncategorizedSkill)]
        PR[(PlacementRecord)]
    end

    SD --> API_SVC
    CD --> API_SVC
    AD --> API_SVC
    SD --> SC
    CD --> SC
    AD --> SC

    API_SVC -->|GET /api/dashboard/student| DR
    API_SVC -->|GET /api/dashboard/coordinator| DR
    API_SVC -->|GET /api/dashboard/admin| DR

    DR --> AUTH
    DR --> DS
    DS --> AS
    DS --> JM
    DS --> PS
    DS --> U
    DS --> SP
    DS --> JR
    DS --> CO
    DS --> SL
    DS --> ST
    DS --> US
    DS --> PR
```

### Request Flow

1. User logs in → frontend redirects to role-appropriate dashboard route.
2. Dashboard component mounts → calls `api.get('/dashboard/<role>')`.
3. Backend route validates JWT + role via decorators.
4. `DashboardService` method aggregates data from models and existing services.
5. JSON response returned → frontend renders summary cards, metrics, quick actions.

## Components and Interfaces

### Backend

#### `backend/app/routes/dashboard_routes.py`

New Flask Blueprint `dashboard_bp` with prefix `/api/dashboard`.

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/dashboard/student` | GET | `@jwt_required @role_required("student")` | Returns student dashboard summary |
| `/api/dashboard/coordinator` | GET | `@jwt_required @role_required("placement_officer")` | Returns coordinator dashboard summary |
| `/api/dashboard/admin` | GET | `@jwt_required @role_required("admin")` | Returns admin dashboard summary |

Each route handler delegates to `DashboardService` and returns the result as JSON.

#### `backend/app/services/dashboard_service.py`

New service class `DashboardService` with three public methods:

```python
class DashboardService:
    def get_student_summary(self, user_id: int) -> dict:
        """Aggregate student dashboard data."""
        ...

    def get_coordinator_summary(self) -> dict:
        """Aggregate coordinator/placement officer dashboard data."""
        ...

    def get_admin_summary(self) -> dict:
        """Aggregate admin dashboard data."""
        ...
```

**`get_student_summary(user_id)` returns:**
```python
{
    "profile_completeness": 75,          # int 0-100
    "skill_count": 12,                   # int
    "skill_breakdown": {                  # dict[str, int]
        "Programming Languages": 4,
        "Frameworks": 3,
        "Databases": 2,
        "Tools": 3
    },
    "matched_job_count": 8,              # int
    "top_recommendations": [             # list (max 3)
        {
            "job_role_id": 1,
            "title": "Backend Developer",
            "company_name": "TechCorp",
            "compatibility_score": 87.5
        }
    ]
}
```

**Profile completeness calculation**: Checks the following fields on `StudentProfile`: `institution`, `degree`, `branch`, `cgpa`, `graduation_year`, `skills_json`. Each non-null/non-empty field contributes equally. Also checks that at least one project and one certification exist. Formula: `filled_fields / total_fields * 100`, rounded to nearest integer. Total fields = 8 (6 profile fields + has_projects + has_certifications).

**`get_coordinator_summary()` returns:**
```python
{
    "placement_overview": {
        "total_students": 150,
        "placed_students": 45,
        "total_companies": 20,
        "placement_percentage": 30.0
    },
    "active_job_count": 12,
    "shortlisted_count": 35,
    "recent_shortlists": [               # list (max 5)
        {
            "student_name": "Alice",
            "job_title": "Backend Dev",
            "company_name": "TechCorp",
            "compatibility_score": 87.5,
            "shortlisted_at": "2024-01-15T10:30:00"
        }
    ],
    "top_skills_demand": [               # list (max 5)
        {"skill": "Python", "count": 8}
    ]
}
```

**`get_admin_summary()` returns:**
```python
{
    "user_counts": {
        "by_role": {
            "student": 150,
            "placement_officer": 5,
            "admin": 2
        },
        "by_status": {
            "active": 152,
            "inactive": 5
        },
        "total": 157
    },
    "taxonomy_health": {
        "total_skills": 85,
        "deprecated_skills": 3,
        "uncategorized_pending": 12
    },
    "placement_overview": {
        "total_students": 150,
        "placed_students": 45,
        "total_companies": 20,
        "placement_percentage": 30.0
    }
}
```

### Frontend

#### Shared Components

**`frontend/src/components/SummaryCard.tsx`**
A reusable card component displaying a label and value:

```typescript
interface SummaryCardProps {
  label: string;
  value: string | number;
  highlight?: boolean;  // optional visual emphasis
}
```

#### Dashboard Pages

**`frontend/src/pages/student/Dashboard.tsx`** (rewrite)
- Fetches `GET /api/dashboard/student` on mount.
- Renders: profile completeness card (with highlight if < 100%), skill count card, matched jobs card, skill breakdown list, top 3 recommendations list, quick-action links.
- Shows loading spinner while fetching.
- Shows error message with retry button on failure.
- Shows empty-state prompts when profile is incomplete or no jobs exist.

**`frontend/src/pages/admin/Dashboard.tsx`** (rewrite, serves both coordinator and admin)
- Checks `user.role` to determine which endpoint to call (`/dashboard/coordinator` or `/dashboard/admin`).
- **Coordinator view**: placement overview cards, active jobs card, shortlisted count card, recent shortlists table, top skills demand list, quick-action links.
- **Admin view**: user count cards (by role, by status), taxonomy health cards, placement overview cards, quick-action links with admin-only actions visually distinguished.
- Shows loading spinner while fetching.
- Shows error message with retry button on failure.

#### Routing

No routing changes needed. The existing routes in `App.tsx` already map:
- `/student/dashboard` → `StudentDashboard`
- `/admin/dashboard` → `AdminDashboard`

The `AdminDashboard` component internally switches between coordinator and admin views based on `user.role`.

## Data Models

No new database models are required. All dashboard data is derived from existing models:

| Model | Dashboard Usage |
|---|---|
| `User` | Admin: user counts by role and status |
| `StudentProfile` | Student: profile completeness, skill data |
| `JobRole` | Student: matched job count; Coordinator: active job count; All: skill demand |
| `Company` | Coordinator: company count (via `AnalyticsService`) |
| `Shortlist` | Coordinator: shortlisted count, recent shortlists |
| `SkillTaxonomy` | Student: skill categorization; Admin: taxonomy health |
| `UncategorizedSkill` | Admin: pending review count |
| `PlacementRecord` | Coordinator/Admin: placement statistics |

### Response Schemas (TypeScript)

```typescript
interface StudentDashboardResponse {
  profile_completeness: number;
  skill_count: number;
  skill_breakdown: Record<string, number>;
  matched_job_count: number;
  top_recommendations: Array<{
    job_role_id: number;
    title: string;
    company_name: string;
    compatibility_score: number;
  }>;
}

interface CoordinatorDashboardResponse {
  placement_overview: {
    total_students: number;
    placed_students: number;
    total_companies: number;
    placement_percentage: number;
  };
  active_job_count: number;
  shortlisted_count: number;
  recent_shortlists: Array<{
    student_name: string;
    job_title: string;
    company_name: string;
    compatibility_score: number;
    shortlisted_at: string;
  }>;
  top_skills_demand: Array<{
    skill: string;
    count: number;
  }>;
}

interface AdminDashboardResponse {
  user_counts: {
    by_role: Record<string, number>;
    by_status: Record<string, number>;
    total: number;
  };
  taxonomy_health: {
    total_skills: number;
    deprecated_skills: number;
    uncategorized_pending: number;
  };
  placement_overview: {
    total_students: number;
    placed_students: number;
    total_companies: number;
    placement_percentage: number;
  };
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The following properties were derived from the acceptance criteria through prework analysis. Criteria related to UI rendering, navigation, loading states, and specific edge cases are covered by example-based tests rather than property-based tests.

### Property 1: Profile completeness is bounded

*For any* `StudentProfile` with any combination of filled and empty fields (institution, degree, branch, cgpa, graduation_year, skills_json, projects, certifications), the computed `profile_completeness` value SHALL be an integer in the range [0, 100].

**Validates: Requirements 1.1**

### Property 2: Skill breakdown consistency

*For any* student profile with a non-empty skills list, the `skill_breakdown` dictionary's values SHALL each equal the actual count of the student's extracted skills in that category, and the sum of all category counts SHALL equal `skill_count`.

**Validates: Requirements 1.2, 3.1**

### Property 3: Matched job count equals eligible active jobs

*For any* student with a given CGPA and skill vector, and any set of active job roles with varying CGPA thresholds, the `matched_job_count` SHALL equal the number of active job roles where the student's CGPA meets or exceeds the job's `cgpa_threshold` and the job has a valid job vector.

**Validates: Requirements 1.3**

### Property 4: Top recommendations are sorted and limited

*For any* non-empty set of job recommendations for a student, the `top_recommendations` list SHALL contain at most 3 items, and the items SHALL be sorted by `compatibility_score` in descending order.

**Validates: Requirements 1.4**

### Property 5: Coordinator counts match database state

*For any* database state with job roles and shortlist records, the coordinator dashboard's `active_job_count` SHALL equal the count of `JobRole` records where `is_active=True`, and `shortlisted_count` SHALL equal the total count of `Shortlist` records.

**Validates: Requirements 4.2**

### Property 6: Recent shortlists are sorted and limited

*For any* set of shortlist records in the database, the coordinator dashboard's `recent_shortlists` SHALL contain at most 5 items, and the items SHALL be sorted by `shortlisted_at` in descending order (most recent first).

**Validates: Requirements 5.1**

### Property 7: Top skills demand is sorted and limited

*For any* set of active job roles with `required_skills_json`, the coordinator dashboard's `top_skills_demand` SHALL contain at most 5 items, and the items SHALL be sorted by `count` in descending order.

**Validates: Requirements 5.3**

### Property 8: User counts correctness with sum invariant

*For any* set of users in the database with varying roles and statuses, the admin dashboard's `user_counts.by_role` values SHALL each match the actual count of users with that role, `user_counts.by_status` values SHALL each match the actual count of users with that status, and the sum of `by_role` values SHALL equal `user_counts.total`.

**Validates: Requirements 7.1, 11.3**

### Property 9: Taxonomy health counts correctness

*For any* set of `SkillTaxonomy` and `UncategorizedSkill` records, the admin dashboard's `taxonomy_health.total_skills` SHALL equal the count of non-deprecated taxonomy entries, `deprecated_skills` SHALL equal the count of deprecated entries, and `uncategorized_pending` SHALL equal the count of unreviewed `UncategorizedSkill` records.

**Validates: Requirements 7.2**

### Property 10: Student dashboard response round-trip serialization

*For any* valid student dashboard response dictionary (containing profile_completeness, skill_count, skill_breakdown, matched_job_count, and top_recommendations), serializing to JSON and deserializing back SHALL produce an equivalent data structure.

**Validates: Requirements 11.1**

### Property 11: Dashboard placement overview matches analytics service

*For any* database state with placement records, the coordinator dashboard's `placement_overview` values (total_students, placed_students, total_companies, placement_percentage) SHALL be identical to the values returned by `AnalyticsService.get_overview_stats()` for the same database state.

**Validates: Requirements 11.2**

## Error Handling

### Backend

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Missing/invalid JWT token | 401 | `AUTHENTICATION_ERROR` | "Missing or invalid Authorization header" |
| Wrong role for endpoint | 403 | `AUTHORIZATION_ERROR` | "Insufficient permissions" |
| Student has no profile | 200 | — | Returns response with `profile_completeness: 0`, empty skill data, and zero counts |
| Database query failure | 500 | `INTERNAL_ERROR` | "An unexpected error occurred" |

Design decision: The student dashboard endpoint returns a valid response even when the student has no profile (with zeroed-out values) rather than a 404. This avoids a broken dashboard for new users who haven't set up their profile yet.

### Frontend

| Scenario | Behavior |
|---|---|
| API returns 401 | Existing axios interceptor clears token and redirects to `/login` |
| API returns 403 | Display "You don't have permission to view this dashboard" message |
| API returns 5xx or network error | Display error message with "Retry" button |
| API call in progress | Display loading spinner (CSS class `dash-loading`) |
| Retry button clicked | Re-invoke the dashboard API call |

## Testing Strategy

### Property-Based Tests (Backend)

Property-based testing is appropriate for this feature because the `DashboardService` methods are aggregation functions with clear input/output behavior. The input space (varying combinations of profile fields, job roles, skills, users) is large, and universal properties (bounds, sorting, invariants, round-trips) hold across all valid inputs.

- **Library**: [Hypothesis](https://hypothesis.readthedocs.io/) for Python
- **Location**: `backend/tests/property/test_dashboard_properties.py`
- **Configuration**: Minimum 100 iterations per property test
- **Tag format**: `# Feature: role-based-dashboards, Property {N}: {title}`

Each of the 11 correctness properties above maps to a single Hypothesis test function. Tests will use the `@given` decorator with custom strategies to generate random database states (profiles, job roles, users, shortlists, taxonomy entries) and verify the properties against `DashboardService` methods.

### Unit Tests (Backend)

- **Location**: `backend/tests/unit/test_dashboard_service.py`
- Specific examples:
  - Student with no profile → completeness 0%, empty skills, zero job matches
  - Student with fully complete profile → completeness 100%
  - Coordinator with no shortlists → empty recent_shortlists list
  - Admin with no users → all counts zero
  - Edge case: student with skills but no active job roles → matched_job_count 0
- Auth/role enforcement:
  - Unauthenticated request → 401
  - Student requesting coordinator endpoint → 403
  - Placement officer requesting admin endpoint → 403

### Integration Tests (Backend)

- **Location**: `backend/tests/integration/test_dashboard_routes.py`
- End-to-end tests through Flask test client:
  - Authenticated student GET `/api/dashboard/student` → 200 with expected shape
  - Authenticated coordinator GET `/api/dashboard/coordinator` → 200 with expected shape
  - Authenticated admin GET `/api/dashboard/admin` → 200 with expected shape
  - Verify response times are reasonable (< 3 seconds for seeded data)

### Frontend Tests

- Component rendering tests for each dashboard variant (student, coordinator, admin)
- Verify loading state, error state with retry, and empty states
- Verify quick-action links are present and correctly routed
- Verify admin-only actions are visually distinguished
