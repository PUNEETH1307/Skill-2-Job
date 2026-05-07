"""Analytics service for the Skill2Job Placement System.

Provides aggregate placement statistics, department and company breakdowns,
and skill demand analysis.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
"""

import json
from datetime import date

from sqlalchemy import func

from app import db
from app.models import (
    User,
    StudentProfile,
    Company,
    JobRole,
    PlacementRecord,
)


class AnalyticsService:
    """Computes placement analytics and statistics."""

    def get_overview_stats(self) -> dict:
        """Return aggregate placement statistics.

        Returns:
            dict with total_students, placed_students, total_companies,
            and placement_percentage.
        """
        total_students = User.query.filter_by(role="student").count()
        placed_students = (
            db.session.query(func.count(func.distinct(PlacementRecord.profile_id)))
            .scalar()
        ) or 0
        total_companies = Company.query.count()

        placement_percentage = 0.0
        if total_students > 0:
            placement_percentage = round((placed_students / total_students) * 100, 2)

        return {
            "total_students": total_students,
            "placed_students": placed_students,
            "total_companies": total_companies,
            "placement_percentage": placement_percentage,
        }

    def get_department_breakdown(
        self, date_from: date = None, date_to: date = None
    ) -> list[dict]:
        """Return placement counts grouped by department.

        Args:
            date_from: Optional start date filter.
            date_to: Optional end date filter.

        Returns:
            List of dicts with department, count, and percentage.
        """
        query = db.session.query(
            PlacementRecord.department,
            func.count(PlacementRecord.id).label("count"),
        )

        if date_from:
            query = query.filter(PlacementRecord.placement_date >= date_from)
        if date_to:
            query = query.filter(PlacementRecord.placement_date <= date_to)

        results = query.group_by(PlacementRecord.department).all()

        total = sum(r.count for r in results) if results else 0

        breakdown = []
        for r in results:
            dept_name = r.department or "Unknown"
            percentage = round((r.count / total) * 100, 2) if total > 0 else 0.0
            breakdown.append({
                "department": dept_name,
                "count": r.count,
                "percentage": percentage,
            })

        return breakdown

    def get_company_breakdown(
        self, date_from: date = None, date_to: date = None
    ) -> list[dict]:
        """Return placement counts grouped by company.

        Args:
            date_from: Optional start date filter.
            date_to: Optional end date filter.

        Returns:
            List of dicts with company_id, company_name, and count.
        """
        query = db.session.query(
            Company.id,
            Company.name,
            func.count(PlacementRecord.id).label("count"),
        ).join(PlacementRecord, PlacementRecord.company_id == Company.id)

        if date_from:
            query = query.filter(PlacementRecord.placement_date >= date_from)
        if date_to:
            query = query.filter(PlacementRecord.placement_date <= date_to)

        results = query.group_by(Company.id, Company.name).all()

        return [
            {
                "company_id": r.id,
                "company_name": r.name,
                "count": r.count,
            }
            for r in results
        ]

    def get_skill_demand(self) -> list[dict]:
        """Return most frequently required skills across active job roles.

        Aggregates required_skills_json from all active JobRoles, counts
        frequency of each skill, and returns sorted descending.

        Returns:
            List of dicts with skill and count, sorted by count descending.
        """
        active_jobs = JobRole.query.filter_by(is_active=True).all()

        skill_counts: dict[str, int] = {}
        for job in active_jobs:
            if not job.required_skills_json:
                continue
            try:
                skills = json.loads(job.required_skills_json)
            except (json.JSONDecodeError, TypeError):
                continue
            for skill in skills:
                normalized = skill.strip()
                if normalized:
                    skill_counts[normalized] = skill_counts.get(normalized, 0) + 1

        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"skill": name, "count": count} for name, count in sorted_skills]
