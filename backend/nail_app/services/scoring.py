from collections import Counter
from datetime import date
from django.db.models import Avg


def score_visit_recency(days_since_visit):
    if days_since_visit is None:
        return 30
    if days_since_visit <= 15:
        return 5
    elif days_since_visit <= 30:
        return 15
    elif days_since_visit <= 45:
        return 25
    elif days_since_visit <= 60:
        return 35
    elif days_since_visit <= 90:
        return 45
    return 55


def score_cancel_rate(cancel_count, total_appt=0):
    if cancel_count == 0:
        return 0
    elif cancel_count == 1:
        return 15
    elif cancel_count == 2:
        return 25
    elif cancel_count <= 4:
        return 35
    return 50


def score_satisfaction_drop(satisfaction_drop):
    if satisfaction_drop is None or satisfaction_drop <= 0:
        return 0
    elif satisfaction_drop <= 0.5:
        return 15
    elif satisfaction_drop <= 1:
        return 25
    elif satisfaction_drop <= 1.5:
        return 40
    return 55


def score_preference_match(color_match, style_match):
    if not color_match and not style_match:
        return 40
    elif not color_match or not style_match:
        return 20
    return 0


def score_duration_stability(avg_duration):
    if avg_duration is None:
        return 10
    if avg_duration >= 25:
        return 0
    elif avg_duration >= 20:
        return 10
    elif avg_duration >= 15:
        return 20
    elif avg_duration >= 10:
        return 35
    return 50


def score_design_shape(nail_shape, hand_shape, nail_length, hand_shape_map, length_shape_map):
    score = 0
    if nail_shape in hand_shape_map.get(hand_shape, []):
        score += 50
    if nail_shape in length_shape_map.get(nail_length, []):
        score += 50
    return score


def score_design_color(color_system, skin_tone, preferred_colors, skin_tone_color_map):
    score = 0
    tone_colors = skin_tone_color_map.get(skin_tone, [])
    for c in tone_colors:
        if c in color_system:
            score += 30
            break
    if preferred_colors:
        pref_list = [c.strip() for c in preferred_colors.split(',') if c.strip()]
        for pc in pref_list:
            if pc[:1] in color_system or pc[:2] in color_system:
                score += 70
                break
    return min(score, 100)


def score_design_decoration(decoration, past_decors, has_high_satisfaction=False):
    score = 0
    if past_decors:
        for pd in past_decors:
            if pd and pd in decoration:
                score += 50
                break
        if has_high_satisfaction:
            score += 50
    return min(score, 100) if score > 0 else 20


def score_design_style(design_tags, pref_styles, history_tags):
    score = 0
    pref_list = [s.strip() for s in pref_styles.split(',') if s.strip()] if pref_styles else []
    for ps in pref_list:
        if ps in design_tags:
            score += 60
            break
    for ht in history_tags:
        if ht in design_tags:
            score += 40
            break
    return min(score, 100) if score > 0 else 25


def score_design_occasion(design_occasion, target_occasion):
    if not target_occasion:
        return 40
    if design_occasion == target_occasion:
        return 100
    related = {
        'party': ['date', 'festival', 'wedding'],
        'wedding': ['party', 'date', 'festival'],
        'date': ['party', 'wedding'],
        'festival': ['party', 'travel'],
        'travel': ['festival', 'daily'],
        'office': ['daily'],
        'daily': ['office', 'travel'],
    }
    if design_occasion in related.get(target_occasion, []):
        return 50
    return 10


def score_design_satisfaction(avg_sat, appt_count=0):
    if avg_sat is None:
        return 60
    score = avg_sat * 20
    if appt_count > 5:
        score = min(score + 10, 100)
    return round(score, 1)


def score_design_budget(design_price, budget, budget_ranges):
    if not budget:
        return 80
    min_price, max_price = budget_ranges.get(budget, (0, 999999))
    try:
        price = float(design_price)
    except (TypeError, ValueError):
        price = 0
    if min_price <= price <= max_price:
        return 100
    elif price < min_price:
        return 70
    return round(max(0, 100 - (price - max_price) / 10), 1)


def weighted_score(scores, weights):
    total = 0.0
    for key, weight in weights.items():
        total += scores.get(key, 0) * weight
    return round(total, 1)
