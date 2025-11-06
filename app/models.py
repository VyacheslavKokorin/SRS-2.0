from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from . import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interval_multiplier = db.Column(db.Float, default=2.0)
    initial_interval_minutes = db.Column(db.Integer, default=5)

    cards = db.relationship("Card", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    word = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    examples = db.relationship(
        "Example",
        backref="card",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Example.created_at",
    )

    def average_interval(self, direction: str) -> float:
        relevant = [ex.interval_minutes for ex in self.examples if ex.direction == direction]
        if not relevant:
            return 0.0
        return sum(relevant) / len(relevant)


class Example(db.Model):
    __tablename__ = "examples"

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("card.id"), nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # EN_RU or RU_EN
    prefix = db.Column(db.String(255), nullable=False)
    focus = db.Column(db.String(120), nullable=False)
    suffix = db.Column(db.String(255), nullable=False)
    translation = db.Column(db.String(255), nullable=False)
    interval_minutes = db.Column(db.Float, nullable=False)
    next_review_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def mark_correct(self, multiplier: float) -> None:
        self.interval_minutes = max(1.0, self.interval_minutes * multiplier)
        self.next_review_at = datetime.utcnow() + timedelta(minutes=self.interval_minutes)

    def mark_incorrect(self, initial_interval: int) -> None:
        self.interval_minutes = float(initial_interval)
        self.next_review_at = datetime.utcnow() + timedelta(minutes=self.interval_minutes)

    @property
    def full_sentence(self) -> str:
        return f"{self.prefix} {self.focus} {self.suffix}".strip()


class SettingsHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    interval_multiplier = db.Column(db.Float)
    initial_interval_minutes = db.Column(db.Integer)
