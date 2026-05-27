"""
Review & Rating business logic.

- Create a review for a resolved consultation
- Fetch doctor reviews
- Compute rating summary statistics
"""
from typing import Dict, List, Optional

from ..extensions import db
from ..models import Review, Consultation, User


def create_review(
    patient_id: int,
    consultation_id: int,
    rating: int,
    comment: Optional[str] = None,
) -> Review:
    """
    Create a review for a doctor after a resolved consultation.
    Raises ValueError if validation fails.
    """
    consultation = Consultation.query.get(consultation_id)
    if consultation is None:
        raise ValueError("Consultation not found")

    if consultation.patient_id != patient_id:
        raise ValueError("You can only review consultations you created")

    if consultation.status != "resolved":
        raise ValueError("You can only review resolved consultations")

    # Check for existing review
    existing = Review.query.filter_by(consultation_id=consultation_id).first()
    if existing:
        raise ValueError("You have already reviewed this consultation")

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise ValueError("Rating must be an integer between 1 and 5")

    review = Review(
        patient_id=patient_id,
        doctor_id=consultation.doctor_id,
        consultation_id=consultation_id,
        rating=rating,
        comment=(comment or "").strip() or None,
    )
    db.session.add(review)
    db.session.commit()
    db.session.refresh(review)
    return review


def get_doctor_reviews(doctor_id: int) -> List[Review]:
    """Return all reviews for a doctor, newest first."""
    return (
        Review.query.filter_by(doctor_id=doctor_id)
        .order_by(Review.created_at.desc())
        .all()
    )


def get_doctor_rating_summary(doctor_id: int) -> Dict:
    """
    Return rating summary for a doctor:
    - average_rating
    - total_reviews
    - distribution counts (1-5 stars)
    """
    reviews = Review.query.filter_by(doctor_id=doctor_id).all()
    total = len(reviews)
    if total == 0:
        return {
            "doctor_id": doctor_id,
            "average_rating": 0.0,
            "total_reviews": 0,
            "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

    total_score = sum(r.rating for r in reviews)
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        if 1 <= r.rating <= 5:
            distribution[r.rating] += 1

    return {
        "doctor_id": doctor_id,
        "average_rating": round(total_score / total, 2),
        "total_reviews": total,
        "distribution": distribution,
    }
