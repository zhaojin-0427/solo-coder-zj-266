from datetime import datetime
from django.db.models import Count, Q, Avg
from ..models import (
    CustomerPreference, NailWork, NailDesign, Appointment
)
from ..serializers import NailDesignSerializer


def get_current_season():
    month = datetime.now().month
    if month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'autumn'
    return 'winter'


SEASON_COLORS = {
    'spring': ['粉', '绿', '黄', '淡', '清', '花'],
    'summer': ['蓝', '白', '薄荷', '清', '冰', '浅'],
    'autumn': ['焦糖', '棕', '橘', '红棕', '奶茶', '咖'],
    'winter': ['红', '金', '酒红', '墨绿', '深', '闪'],
}


def get_customer_recommendations(customer):
    pref, _ = CustomerPreference.objects.get_or_create(customer=customer)
    works = NailWork.objects.filter(customer=customer)
    designs = NailDesign.objects.all()

    season = get_current_season()
    season_colors = SEASON_COLORS.get(season, [])

    pref_colors = [c.strip() for c in pref.preferred_colors.split(',') if c.strip()]
    pref_styles = [s.strip() for s in pref.preferred_styles.split(',') if s.strip()]
    pref_shapes = [s.strip() for s in pref.preferred_shapes.split(',') if s.strip()]

    past_colors = list(works.values_list('actual_color', flat=True))
    past_tags = set()
    for w in works:
        if w.design:
            past_tags.update(t.name for t in w.design.style_tags.all())

    scored = []
    for d in designs:
        score = 0
        reasons = []

        d_colors_lower = d.color_system.lower()
        for c in pref_colors:
            if c.lower() in d_colors_lower:
                score += 5
                reasons.append(f'匹配偏好色系：{c}')

        for c in past_colors:
            if c and c.lower() in d_colors_lower:
                score += 3
                reasons.append(f'匹配历史色系')

        for c in season_colors:
            if c in d.color_system:
                score += 4
                reasons.append(f'当季推荐：{c}色系')

        d_tags = set(t.name for t in d.style_tags.all())
        for s in pref_styles:
            if s in d_tags:
                score += 5
                reasons.append(f'匹配偏好风格：{s}')

        for t in past_tags:
            if t in d_tags:
                score += 3
                reasons.append(f'匹配历史风格')

        if d.nail_shape in pref_shapes:
            score += 4
            reasons.append(f'匹配偏好甲型')

        appt_count = Appointment.objects.filter(design=d, status='completed').count()
        if appt_count > 0:
            score += min(appt_count, 5)
            reasons.append(f'热门款式（{appt_count}次预约）')

        if score > 0:
            scored.append({
                'design': NailDesignSerializer(d).data,
                'score': score,
                'reasons': reasons[:3]
            })

    scored.sort(key=lambda x: x['score'], reverse=True)
    return {
        'season': season,
        'season_colors': season_colors,
        'recommendations': scored[:10]
    }
