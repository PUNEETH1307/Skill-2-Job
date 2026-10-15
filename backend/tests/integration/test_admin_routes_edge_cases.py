"""Branch coverage tests for admin routes."""

import bcrypt

from app import db
from app.models import Company, JobRole, SkillTaxonomy, User
from tests.integration.test_admin_routes import (
    _auth_header,
    _create_company,
    _create_placement_officer,
)


def _create_admin(client):
    password_hash = bcrypt.hashpw(b"adminpass123", bcrypt.gensalt()).decode("utf-8")
    db.session.add(
        User(
            name="Admin User",
            email="admin-edge@example.com",
            password_hash=password_hash,
            role="admin",
            status="active",
        )
    )
    db.session.commit()
    response = client.post(
        "/api/auth/login",
        json={"email": "admin-edge@example.com", "password": "adminpass123"},
    )
    return response.get_json()["token"]


def test_company_routes_cover_invalid_json_and_all_updates(client):
    token = _create_placement_officer(client)
    response = client.post(
        "/api/admin/companies",
        data="{",
        content_type="application/json",
        headers=_auth_header(token),
    )
    assert response.status_code == 400

    company_id = _create_company(client, token).get_json()["id"]
    response = client.put(
        f"/api/admin/companies/{company_id}",
        data="{",
        content_type="application/json",
        headers=_auth_header(token),
    )
    assert response.status_code == 400
    response = client.put(
        f"/api/admin/companies/{company_id}",
        json={"name": "Updated", "industry": "IT", "location": "Mysuru",
              "contact_email": "new@example.com", "contact_phone": "123"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    response = client.put(
        f"/api/admin/companies/{company_id}",
        json={"name": ""},
        headers=_auth_header(token),
    )
    assert response.status_code == 400


def test_job_routes_cover_validation_and_vector_failure(client, monkeypatch):
    token = _create_placement_officer(client)
    company_id = _create_company(client, token).get_json()["id"]
    response = client.post(
        "/api/admin/jobs",
        data="{",
        content_type="application/json",
        headers=_auth_header(token),
    )
    assert response.status_code == 400
    response = client.post(
        "/api/admin/jobs",
        json={"company_id": company_id},
        headers=_auth_header(token),
    )
    assert response.status_code == 400

    def fail_vector(self, skills):
        raise RuntimeError("vector failure")

    monkeypatch.setattr(
        "app.services.skill_analyzer.SkillAnalyzer.generate_job_requirement_vector",
        fail_vector,
    )
    response = client.post(
        "/api/admin/jobs",
        json={"company_id": company_id, "title": "Role", "required_skills": ["Python"]},
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    job_id = response.get_json()["id"]

    response = client.get("/api/admin/jobs", headers=_auth_header(token))
    assert response.status_code == 200
    orphan = JobRole(title="Orphan", company_id=99999, is_active=True)
    db.session.add(orphan)
    db.session.commit()
    assert any(item["company_name"] is None for item in client.get(
        "/api/admin/jobs", headers=_auth_header(token)
    ).get_json())

    response = client.put(
        f"/api/admin/jobs/{job_id}",
        data="{",
        content_type="application/json",
        headers=_auth_header(token),
    )
    assert response.status_code == 400
    response = client.put(
        f"/api/admin/jobs/{job_id}",
        json={"title": "", "description": "x"},
        headers=_auth_header(token),
    )
    assert response.status_code == 400
    response = client.put(
        f"/api/admin/jobs/{job_id}",
        json={"title": "Updated", "description": "x", "cgpa_threshold": 8,
              "academic_status": "active", "is_active": False,
              "required_skills": []},
        headers=_auth_header(token),
    )
    assert response.status_code == 200


def test_job_update_regenerates_vector_and_handles_bad_old_vector(client, monkeypatch):
    token = _create_placement_officer(client)
    company_id = _create_company(client, token).get_json()["id"]
    job_id = client.post(
        "/api/admin/jobs",
        json={"company_id": company_id, "title": "Role",
              "required_skills": ["Python"]},
        headers=_auth_header(token),
    ).get_json()["id"]
    job = db.session.get(JobRole, job_id)
    job.required_skills_json = "{"
    db.session.commit()

    class Vector:
        def tolist(self):
            return [1, 0]

    monkeypatch.setattr(
        "app.services.skill_analyzer.SkillAnalyzer.generate_job_requirement_vector",
        lambda self, skills: Vector(),
    )
    response = client.put(
        f"/api/admin/jobs/{job_id}",
        json={"required_skills": ["Java"], "title": "Updated"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    monkeypatch.setattr(
        "app.services.skill_analyzer.SkillAnalyzer.generate_job_requirement_vector",
        lambda self, skills: (_ for _ in ()).throw(RuntimeError("vector failure")),
    )
    response = client.put(
        f"/api/admin/jobs/{job_id}",
        json={"required_skills": ["Go"]},
        headers=_auth_header(token),
    )
    assert response.status_code == 200


def test_shortlist_email_failure_is_non_fatal(client, monkeypatch):
    token = _create_placement_officer(client)
    company_id = _create_company(client, token).get_json()["id"]
    job_id = client.post(
        "/api/admin/jobs",
        json={"company_id": company_id, "title": "Role"},
        headers=_auth_header(token),
    ).get_json()["id"]
    student = User(
        name="Student",
        email="shortlist@example.com",
        password_hash="hash",
        role="student",
        status="active",
    )
    db.session.add(student)
    db.session.flush()
    from app.models import StudentProfile
    profile = StudentProfile(user_id=student.id, cgpa=8.0)
    db.session.add(profile)
    db.session.commit()

    monkeypatch.setattr(
        "app.routes.admin_routes.JobMatchingEngine.shortlist_candidates",
        lambda self, role_id: [{"profile_id": profile.id, "compatibility_score": 0.8}],
    )

    class FailingEmailService:
        def send_shortlist_notification(self, **kwargs):
            raise RuntimeError("mail unavailable")

    monkeypatch.setattr(
        "app.services.email_service.get_email_service",
        lambda: FailingEmailService(),
    )
    response = client.post(
        f"/api/admin/jobs/{job_id}/shortlist",
        json={"profile_ids": [profile.id]},
        headers=_auth_header(token),
    )
    assert response.status_code == 201


def test_analytics_and_user_validation_edges(client):
    officer = _create_placement_officer(client)
    response = client.get(
        "/api/admin/analytics?date_to=not-a-date",
        headers=_auth_header(officer),
    )
    assert response.status_code == 400

    admin = _create_admin(client)
    response = client.post(
        "/api/admin/users",
        data="{",
        content_type="application/json",
        headers=_auth_header(admin),
    )
    assert response.status_code == 400
    response = client.post(
        "/api/admin/users",
        json={"name": "", "email": "", "password": "short", "role": "bad"},
        headers=_auth_header(admin),
    )
    assert response.status_code == 400

    user = User(
        name="Inactive Target",
        email="inactive-target@example.com",
        password_hash="hash",
        role="student",
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    response = client.put(
        f"/api/admin/users/{user.id}/status",
        data="{",
        content_type="application/json",
        headers=_auth_header(admin),
    )
    assert response.status_code == 400


def test_predict_student_error_is_returned_as_not_found(client, monkeypatch):
    token = _create_placement_officer(client)

    class Predictor:
        def predict(self, student_id):
            return {"error": "Student not found"}

    monkeypatch.setattr(
        "app.services.placement_predictor.get_predictor", lambda: Predictor()
    )
    response = client.get(
        "/api/admin/predictions/student/999",
        headers=_auth_header(token),
    )
    assert response.status_code == 404


def test_taxonomy_and_course_validation_edges(client):
    admin = _create_admin(client)
    response = client.post(
        "/api/admin/skills/taxonomy",
        data="{",
        content_type="application/json",
        headers=_auth_header(admin),
    )
    assert response.status_code == 400
    response = client.post(
        "/api/admin/skills/taxonomy",
        json={"canonical_name": "Python", "synonyms_json": ["py"]},
        headers=_auth_header(admin),
    )
    assert response.status_code == 201
    skill_id = response.get_json()["id"]
    response = client.put(
        f"/api/admin/skills/taxonomy/{skill_id}",
        data="{",
        content_type="application/json",
        headers=_auth_header(admin),
    )
    assert response.status_code == 400
    response = client.put(
        f"/api/admin/skills/taxonomy/{skill_id}",
        json={"canonical_name": ""},
        headers=_auth_header(admin),
    )
    assert response.status_code == 400
    response = client.put(
        f"/api/admin/skills/taxonomy/{skill_id}",
        json={"canonical_name": "Python 3", "category": "Language",
              "synonyms_json": ["py3"]},
        headers=_auth_header(admin),
    )
    assert response.status_code == 200

    officer = _create_placement_officer(client)
    response = client.post(
        "/api/admin/courses",
        json={"course_name": "Course"},
        headers=_auth_header(officer),
    )
    assert response.status_code == 400
    response = client.post(
        "/api/admin/courses",
        json={"skill_name": "Python"},
        headers=_auth_header(officer),
    )
    assert response.status_code == 400


def test_prediction_routes_delegate_to_predictor(client, monkeypatch):
    token = _create_placement_officer(client)

    class FakePredictor:
        def train(self):
            return {"samples": 1}

        def predict(self, student_id):
            return {"student_id": student_id, "probability": 75}

        def predict_batch(self):
            return [{"student_id": 1, "probability": 75}]

    monkeypatch.setattr(
        "app.services.placement_predictor.get_predictor",
        lambda: FakePredictor(),
    )
    headers = _auth_header(token)
    assert client.post("/api/admin/predictions/train", headers=headers).status_code == 200
    assert client.get("/api/admin/predictions/student/1", headers=headers).status_code == 200
    assert client.get("/api/admin/predictions/batch", headers=headers).get_json() == {
        "predictions": [{"student_id": 1, "probability": 75}]
    }
