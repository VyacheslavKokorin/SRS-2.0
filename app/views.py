from datetime import datetime
from random import choice

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_required, current_user

from . import db
from .forms import (
    CardForm,
    ExampleForm,
    SettingsForm,
    ChangePasswordForm,
    ReviewForm,
    ReviewContinueForm,
)
from .models import Card, Example, SettingsHistory


bp = Blueprint("main", __name__)


def _get_due_examples(user):
    now = datetime.utcnow()
    return (
        Example.query.join(Card)
        .filter(Card.user_id == user.id, Example.next_review_at <= now)
        .order_by(Example.next_review_at)
        .all()
    )


@bp.app_template_filter("format_interval")
def format_interval(minutes):
    if minutes is None:
        return "—"
    minutes = float(minutes)
    if minutes < 60:
        return f"{minutes:.0f} мин"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f} ч"
    days = hours / 24
    return f"{days:.1f} д"


@bp.route("/")
@login_required
def dashboard():
    due_examples = _get_due_examples(current_user)
    total_interval = sum(example.interval_minutes for card in current_user.cards for example in card.examples)
    return render_template(
        "dashboard.html",
        total_interval=total_interval,
        due_count=len(due_examples),
    )


@bp.route("/start-repetition", methods=["GET", "POST"])
@login_required
def start_repetition():
    due_examples = _get_due_examples(current_user)
    form = ReviewForm()
    continue_form = ReviewContinueForm()

    if request.method == "GET":
        if not due_examples:
            flash("Нет карточек для повторения. Добавьте новые или дождитесь интервала.", "info")
            return redirect(url_for("main.dashboard"))
        example = choice(due_examples)
        form.example_id.data = example.id
        return render_template("repetition/review.html", example=example, form=form)

    # Обработка продолжения без проверки ответа
    if continue_form.submit.data and continue_form.validate_on_submit():
        return redirect(url_for("main.start_repetition"))

    if form.validate_on_submit():
        example = Example.query.get(int(form.example_id.data))
        if not example or example.card.user_id != current_user.id:
            flash("Карточка не найдена.", "danger")
            return redirect(url_for("main.start_repetition"))

        answer = form.answer.data.strip().lower()
        correct_answer = example.translation.strip().lower()
        if answer == correct_answer:
            example.mark_correct(current_user.interval_multiplier)
            db.session.commit()
            return render_template(
                "repetition/result.html",
                example=example,
                correct=True,
                continue_form=continue_form,
            )
        else:
            example.mark_incorrect(current_user.initial_interval_minutes)
            db.session.commit()
            flash("Ответ неверный.", "warning")
            return render_template(
                "repetition/result.html",
                example=example,
                correct=False,
                continue_form=continue_form,
            )

    flash("Не удалось обработать попытку. Повторите снова.", "danger")
    return redirect(url_for("main.start_repetition"))


@bp.route("/cards")
@login_required
def cards():
    cards = Card.query.filter_by(user_id=current_user.id).all()
    return render_template("cards/list.html", cards=cards)


@bp.route("/cards/<int:card_id>", methods=["GET", "POST"])
@login_required
def card_detail(card_id):
    card = Card.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
    form = ExampleForm()
    if form.validate_on_submit():
        example = Example(
            card=card,
            direction=form.direction.data,
            prefix=form.prefix.data,
            focus=form.focus.data,
            suffix=form.suffix.data,
            translation=form.translation.data,
            interval_minutes=current_user.initial_interval_minutes,
            next_review_at=datetime.utcnow(),
        )
        db.session.add(example)
        db.session.commit()
        flash("Пример добавлен.", "success")
        return redirect(url_for("main.card_detail", card_id=card.id))
    return render_template("cards/detail.html", card=card, form=form)


@bp.route("/cards/<int:card_id>/delete", methods=["POST"])
@login_required
def delete_card(card_id):
    card = Card.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
    db.session.delete(card)
    db.session.commit()
    flash("Карточка удалена.", "info")
    return redirect(url_for("main.cards"))


@bp.route("/examples/<int:example_id>/delete", methods=["POST"])
@login_required
def delete_example(example_id):
    example = Example.query.get_or_404(example_id)
    if example.card.user_id != current_user.id:
        flash("Нет доступа.", "danger")
        return redirect(url_for("main.cards"))
    card_id = example.card_id
    db.session.delete(example)
    db.session.commit()
    flash("Пример удалён.", "info")
    return redirect(url_for("main.card_detail", card_id=card_id))


@bp.route("/add", methods=["GET", "POST"])
@login_required
def add_card():
    form = CardForm()
    if form.validate_on_submit():
        card = Card(user=current_user, word=form.word.data)
        db.session.add(card)
        db.session.flush()

        initial_interval = current_user.initial_interval_minutes
        now = datetime.utcnow()

        en_example = Example(
            card=card,
            direction="EN_RU",
            prefix=form.en_prefix.data,
            focus=form.en_focus.data,
            suffix=form.en_suffix.data,
            translation=form.en_translation.data,
            interval_minutes=initial_interval,
            next_review_at=now,
        )
        ru_example = Example(
            card=card,
            direction="RU_EN",
            prefix=form.ru_prefix.data,
            focus=form.ru_focus.data,
            suffix=form.ru_suffix.data,
            translation=form.ru_translation.data,
            interval_minutes=initial_interval,
            next_review_at=now,
        )
        db.session.add(en_example)
        db.session.add(ru_example)
        db.session.commit()
        flash("Карточка создана.", "success")
        return redirect(url_for("main.cards"))
    return render_template("cards/add.html", form=form)


@bp.route("/statistics")
@login_required
def statistics():
    cards = Card.query.filter_by(user_id=current_user.id).all()
    total_examples = sum(len(card.examples) for card in cards)
    due_examples = len(_get_due_examples(current_user))
    average_interval = 0.0
    intervals = [example.interval_minutes for card in cards for example in card.examples]
    if intervals:
        average_interval = sum(intervals) / len(intervals)
    return render_template(
        "statistics.html",
        cards=cards,
        total_examples=total_examples,
        due_examples=due_examples,
        average_interval=average_interval,
    )


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings_form = SettingsForm(
        interval_multiplier=current_user.interval_multiplier,
        initial_interval_minutes=current_user.initial_interval_minutes,
    )
    password_form = ChangePasswordForm()

    if settings_form.submit.data and settings_form.validate_on_submit():
        current_user.interval_multiplier = settings_form.interval_multiplier.data
        current_user.initial_interval_minutes = settings_form.initial_interval_minutes.data
        history_entry = SettingsHistory(
            user_id=current_user.id,
            interval_multiplier=current_user.interval_multiplier,
            initial_interval_minutes=current_user.initial_interval_minutes,
        )
        db.session.add(history_entry)
        db.session.commit()
        flash("Настройки обновлены.", "success")
        return redirect(url_for("main.settings"))

    if password_form.submit.data and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Неверный текущий пароль.", "danger")
        else:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Пароль обновлён.", "success")
            return redirect(url_for("main.settings"))

    return render_template(
        "settings.html",
        settings_form=settings_form,
        password_form=password_form,
    )
