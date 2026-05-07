"""Unit tests for the seed script."""

import json
import pytest
import bcrypt

from app.models import User, SkillTaxonomy


# Import seed functions and data
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from seed import (
    seed_skill_taxonomy,
    seed_admin_user,
    SKILL_TAXONOMY,
    ADMIN_EMAIL,
    ADMIN_NAME,
    ADMIN_PASSWORD,
)


@pytest.mark.unit
class TestSeedSkillTaxonomy:
    """Tests for skill taxonomy seeding."""

    def test_seed_creates_all_skills(self, db_session):
        seed_skill_taxonomy()
        count = SkillTaxonomy.query.count()
        assert count == len(SKILL_TAXONOMY)

    def test_seed_covers_all_six_categories(self, db_session):
        seed_skill_taxonomy()
        categories = {s.category for s in SkillTaxonomy.query.all()}
        expected = {
            "Programming Languages",
            "Frameworks",
            "Databases",
            "Tools",
            "Soft Skills",
            "Domain Knowledge",
        }
        assert categories == expected

    def test_seed_stores_synonyms_as_json(self, db_session):
        seed_skill_taxonomy()
        python_skill = SkillTaxonomy.query.filter_by(canonical_name="Python").first()
        assert python_skill is not None
        synonyms = json.loads(python_skill.synonyms_json)
        assert "py" in synonyms

    def test_seed_is_idempotent(self, db_session):
        seed_skill_taxonomy()
        first_count = SkillTaxonomy.query.count()
        seed_skill_taxonomy()
        second_count = SkillTaxonomy.query.count()
        assert first_count == second_count

    def test_seed_synonym_mappings_for_key_skills(self, db_session):
        seed_skill_taxonomy()

        js = SkillTaxonomy.query.filter_by(canonical_name="JavaScript").first()
        assert "JS" in json.loads(js.synonyms_json)

        ts = SkillTaxonomy.query.filter_by(canonical_name="TypeScript").first()
        assert "TS" in json.loads(ts.synonyms_json)

        k8s = SkillTaxonomy.query.filter_by(canonical_name="Kubernetes").first()
        assert "K8s" in json.loads(k8s.synonyms_json)

        pg = SkillTaxonomy.query.filter_by(canonical_name="PostgreSQL").first()
        assert "Postgres" in json.loads(pg.synonyms_json)

        ml = SkillTaxonomy.query.filter_by(canonical_name="Machine Learning").first()
        assert "ML" in json.loads(ml.synonyms_json)

    def test_seed_has_at_least_30_skills(self, db_session):
        seed_skill_taxonomy()
        assert SkillTaxonomy.query.count() >= 30


@pytest.mark.unit
class TestSeedAdminUser:
    """Tests for admin user seeding."""

    def test_seed_creates_admin_user(self, db_session):
        seed_admin_user()
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        assert admin is not None
        assert admin.name == ADMIN_NAME
        assert admin.role == "admin"
        assert admin.status == "active"

    def test_admin_password_is_hashed(self, db_session):
        seed_admin_user()
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        assert admin.password_hash != ADMIN_PASSWORD
        assert bcrypt.checkpw(
            ADMIN_PASSWORD.encode("utf-8"),
            admin.password_hash.encode("utf-8"),
        )

    def test_seed_admin_is_idempotent(self, db_session):
        seed_admin_user()
        seed_admin_user()
        admin_count = User.query.filter_by(email=ADMIN_EMAIL).count()
        assert admin_count == 1
