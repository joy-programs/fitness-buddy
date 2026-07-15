"""
fitness_utils.py — Pure fitness calculation helpers
----------------------------------------------------
No database or AI calls here — just math.
Used by the BMI router and the dashboard service.
"""


def calculate_bmi(height_cm: float, weight_kg: float) -> dict:
    """
    Calculate Body Mass Index (BMI) from height and weight.

    BMI = weight_kg / (height_m ^ 2)

    Returns a dict with:
      - bmi           : rounded to 1 decimal place
      - category      : WHO classification string
      - healthy_range : typical healthy BMI range string
      - disclaimer    : mandatory medical disclaimer
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive values.")

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)
    bmi_rounded = round(bmi, 1)

    # WHO BMI classification
    if bmi_rounded < 18.5:
        category = "Underweight"
    elif bmi_rounded < 25.0:
        category = "Normal weight"
    elif bmi_rounded < 30.0:
        category = "Overweight"
    elif bmi_rounded < 35.0:
        category = "Obesity Class I"
    elif bmi_rounded < 40.0:
        category = "Obesity Class II"
    else:
        category = "Obesity Class III"

    return {
        "bmi": bmi_rounded,
        "category": category,
        "healthy_range": "18.5 – 24.9",
        "disclaimer": (
            "BMI is a basic screening tool and does NOT diagnose health conditions. "
            "It does not account for muscle mass, bone density, age, or ethnicity. "
            "Please consult a qualified healthcare professional for personalised advice."
        ),
    }


def get_calorie_estimate(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str,
) -> dict:
    """
    Rough TDEE (Total Daily Energy Expenditure) estimate using
    the Mifflin–St Jeor equation.

    Returns maintenance calories and a note about its limitations.
    Note: This is only an approximate estimate — NOT clinical nutrition advice.
    """
    # Basal Metabolic Rate
    if gender and gender.lower() in ("male", "m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_multipliers = {
        "sedentary":         1.2,
        "lightly_active":    1.375,
        "moderately_active": 1.55,
        "very_active":       1.725,
    }
    multiplier = activity_multipliers.get(activity_level, 1.2)
    tdee = round(bmr * multiplier)

    return {
        "estimated_maintenance_calories": tdee,
        "note": (
            "This is a rough estimate only. Actual calorie needs vary based on many factors. "
            "Consult a registered dietitian for accurate nutritional guidance."
        ),
    }


def streak_from_habits(habit_dates: list[str]) -> int:
    """
    Given a sorted list of ISO date strings (YYYY-MM-DD) on which
    the user logged at least one habit, return the current streak length.
    """
    from datetime import date, timedelta

    if not habit_dates:
        return 0

    sorted_dates = sorted(set(habit_dates), reverse=True)
    today = date.today()
    streak = 0

    for i, d in enumerate(sorted_dates):
        expected = today - timedelta(days=i)
        if str(expected) == d:
            streak += 1
        else:
            break

    return streak
