"""Placement Success Prediction service for the Skill2Job Placement System.

Uses Random Forest classifier to predict placement probability based on
student features: CGPA, skill count, project count, certification count,
and skill vector coverage.

Requirements: Predictive analytics for placement dashboard
"""

import json
import logging

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app import db
from app.models import StudentProfile, User, PlacementRecord, JobRole

logger = logging.getLogger(__name__)


class PlacementPredictor:
    """Predict placement success probability using Random Forest."""

    def __init__(self):
        self._model = None
        self._is_trained = False

    def train(self) -> dict:
        """Train the Random Forest model on historical placement data.

        Features used:
        - CGPA (normalized 0-10)
        - Skill count
        - Project count
        - Certification count
        - Skill vector density (% of taxonomy skills possessed)

        Labels:
        - 1 = placed (has PlacementRecord)
        - 0 = not placed

        Returns:
            Dict with training stats (samples, accuracy, feature_importances).
        """
        # Fetch all student profiles
        profiles = StudentProfile.query.all()

        if len(profiles) < 5:
            # Not enough data to train — use heuristic model
            self._is_trained = False
            return {"status": "insufficient_data", "samples": len(profiles)}

        # Get placed student profile IDs
        placed_profile_ids = set(
            row[0] for row in
            db.session.query(PlacementRecord.profile_id).distinct().all()
        )

        X = []
        y = []

        for profile in profiles:
            features = self._extract_features(profile)
            X.append(features)
            y.append(1 if profile.id in placed_profile_ids else 0)

        X = np.array(X, dtype=float)
        y = np.array(y, dtype=int)

        # Handle case where all labels are the same
        if len(set(y)) < 2:
            self._is_trained = False
            return {"status": "insufficient_variance", "samples": len(y)}

        # Train Random Forest
        self._model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight="balanced",
        )
        self._model.fit(X, y)
        self._is_trained = True

        # Compute training accuracy
        accuracy = self._model.score(X, y)

        feature_names = [
            "cgpa", "skill_count", "project_count",
            "certification_count", "vector_density"
        ]
        importances = dict(zip(
            feature_names,
            [round(float(v), 4) for v in self._model.feature_importances_]
        ))

        return {
            "status": "trained",
            "samples": len(y),
            "placed_count": int(sum(y)),
            "accuracy": round(float(accuracy), 4),
            "feature_importances": importances,
        }

    def predict(self, student_id: int) -> dict:
        """Predict placement probability for a student.

        Args:
            student_id: The user_id of the student.

        Returns:
            Dict with probability (0-100), confidence, and contributing factors.
        """
        profile = StudentProfile.query.filter_by(user_id=student_id).first()
        if profile is None:
            return {"error": "Profile not found", "probability": 0.0}

        features = self._extract_features(profile)
        features_array = np.array([features], dtype=float)

        if self._is_trained and self._model is not None:
            # Use trained model
            proba = self._model.predict_proba(features_array)[0]
            # proba[1] = probability of class 1 (placed)
            placement_prob = float(proba[1]) * 100
        else:
            # Heuristic fallback when model isn't trained
            placement_prob = self._heuristic_score(features)

        # Determine contributing factors
        factors = self._get_contributing_factors(features)

        return {
            "probability": round(placement_prob, 1),
            "confidence": "high" if self._is_trained else "estimated",
            "model_trained": self._is_trained,
            "factors": factors,
        }

    def predict_batch(self) -> list[dict]:
        """Predict placement probability for all students.

        Returns:
            List of dicts with student_id, name, probability, and factors.
        """
        profiles = StudentProfile.query.all()
        results = []

        for profile in profiles:
            user = db.session.get(User, profile.user_id)
            features = self._extract_features(profile)
            features_array = np.array([features], dtype=float)

            if self._is_trained and self._model is not None:
                proba = self._model.predict_proba(features_array)[0]
                placement_prob = float(proba[1]) * 100
            else:
                placement_prob = self._heuristic_score(features)

            results.append({
                "student_id": profile.user_id,
                "name": user.name if user else "Unknown",
                "cgpa": profile.cgpa,
                "probability": round(placement_prob, 1),
            })

        # Sort by probability descending
        results.sort(key=lambda r: r["probability"], reverse=True)
        return results

    def _extract_features(self, profile: StudentProfile) -> list[float]:
        """Extract feature vector from a student profile.

        Returns:
            [cgpa, skill_count, project_count, cert_count, vector_density]
        """
        cgpa = profile.cgpa or 0.0

        # Skill count
        skill_count = 0
        if profile.skills_json:
            try:
                skills = json.loads(profile.skills_json)
                if isinstance(skills, list):
                    skill_count = len(skills)
            except (json.JSONDecodeError, TypeError):
                pass

        # Project count
        project_count = len(profile.projects) if profile.projects else 0

        # Certification count
        cert_count = len(profile.certifications) if profile.certifications else 0

        # Vector density (what % of taxonomy skills does the student have)
        vector_density = 0.0
        if profile.skill_vector_json:
            try:
                vector_data = json.loads(profile.skill_vector_json)
                vector = vector_data.get("vector", [])
                if vector:
                    vector_density = sum(1 for v in vector if v > 0) / len(vector)
            except (json.JSONDecodeError, TypeError):
                pass

        return [cgpa, skill_count, project_count, cert_count, vector_density]

    def _heuristic_score(self, features: list[float]) -> float:
        """Compute a heuristic placement score when model isn't trained.

        Weighted formula:
        - CGPA: 30% (normalized to 0-100)
        - Skills: 25% (capped at 10 skills = 100%)
        - Projects: 20% (capped at 5 projects = 100%)
        - Certifications: 10% (capped at 3 = 100%)
        - Vector density: 15% (already 0-1)
        """
        cgpa, skill_count, project_count, cert_count, vector_density = features

        cgpa_score = (cgpa / 10.0) * 100
        skill_score = min(skill_count / 10.0, 1.0) * 100
        project_score = min(project_count / 5.0, 1.0) * 100
        cert_score = min(cert_count / 3.0, 1.0) * 100
        density_score = vector_density * 100

        total = (
            0.30 * cgpa_score +
            0.25 * skill_score +
            0.20 * project_score +
            0.10 * cert_score +
            0.15 * density_score
        )

        return min(100.0, max(0.0, total))

    def _get_contributing_factors(self, features: list[float]) -> list[dict]:
        """Identify strengths and weaknesses from features."""
        cgpa, skill_count, project_count, cert_count, vector_density = features
        factors = []

        if cgpa >= 8.0:
            factors.append({"factor": "Strong CGPA", "impact": "positive"})
        elif cgpa < 6.0:
            factors.append({"factor": "Low CGPA", "impact": "negative"})

        if skill_count >= 5:
            factors.append({"factor": "Good skill diversity", "impact": "positive"})
        elif skill_count < 3:
            factors.append({"factor": "Limited skills", "impact": "negative"})

        if project_count >= 3:
            factors.append({"factor": "Strong project portfolio", "impact": "positive"})
        elif project_count == 0:
            factors.append({"factor": "No projects", "impact": "negative"})

        if cert_count >= 2:
            factors.append({"factor": "Certified skills", "impact": "positive"})

        if vector_density >= 0.2:
            factors.append({"factor": "Broad skill coverage", "impact": "positive"})

        return factors


# Module-level singleton for reuse across requests
_predictor = PlacementPredictor()


def get_predictor() -> PlacementPredictor:
    """Get the singleton predictor instance."""
    return _predictor
