import random
from datetime import datetime
from collections import Counter
from django.db.models import Avg
from ..models import (
    NailWork, NailDesign, CustomerPreference,
    SimilarDesignResult, Appointment
)
from .scoring import (
    score_design_shape, score_design_color, score_design_decoration,
    score_design_style, score_design_occasion, score_design_satisfaction,
    score_design_budget, weighted_score
)


SKIN_TONE_COLOR_MATCH = {
    'fair': ['粉', '玫瑰', '白', '裸', '淡', '浅', '蓝', '紫'],
    'light': ['粉', '裸', '白', '奶茶', '玫瑰', '浅', '米', '橘'],
    'medium': ['红', '奶茶', '棕', '橘', '焦糖', '咖', '粉', '玫瑰'],
    'tan': ['焦糖', '棕', '红', '酒红', '金', '咖', '墨绿', '橘'],
    'dark': ['酒红', '金', '墨绿', '深', '红', '咖', '焦糖', '闪'],
}

HAND_SHAPE_SHAPE_MATCH = {
    'slender': ['stiletto', 'almond', 'oval', 'coffin', 'ballerina'],
    'standard': ['squoval', 'oval', 'almond', 'round', 'square'],
    'plump': ['round', 'squoval', 'oval', 'square'],
    'broad': ['square', 'squoval', 'round', 'oval'],
}

NAIL_LENGTH_SHAPE_MATCH = {
    'very_short': ['round', 'squoval', 'square'],
    'short': ['square', 'squoval', 'round', 'oval'],
    'medium': ['oval', 'almond', 'squoval', 'square'],
    'long': ['almond', 'stiletto', 'coffin', 'ballerina', 'oval'],
    'very_long': ['stiletto', 'coffin', 'ballerina', 'almond'],
}

BUDGET_RANGES = {
    'low': (0, 100),
    'medium': (100, 300),
    'high': (300, 600),
    'luxury': (600, 999999),
}


def analyze_hand_features(try_on_task):
    skin_tones = ['fair', 'light', 'medium', 'tan', 'dark']
    hand_shapes = ['slender', 'standard', 'plump', 'broad']
    nail_lengths = ['very_short', 'short', 'medium', 'long', 'very_long']

    analysis_details = {}

    if try_on_task.reference_work:
        work = try_on_task.reference_work
        if work.actual_color:
            color = work.actual_color
            for tone, colors in SKIN_TONE_COLOR_MATCH.items():
                if any(c in color for c in colors):
                    try_on_task.skin_tone = tone
                    analysis_details['skin_tone_source'] = f'基于历史作品色系推断：{color}'
                    break
        if work.design:
            if work.design.nail_shape in HAND_SHAPE_SHAPE_MATCH.get('slender', []):
                try_on_task.hand_shape = random.choice(['slender', 'standard'])
            elif work.design.nail_shape in HAND_SHAPE_SHAPE_MATCH.get('plump', []):
                try_on_task.hand_shape = random.choice(['plump', 'broad', 'standard'])
            else:
                try_on_task.hand_shape = 'standard'
            analysis_details['hand_shape_source'] = f'基于历史作品甲型推断：{work.design.nail_shape}'

            if work.design.nail_shape in ['round', 'squoval', 'square']:
                try_on_task.nail_length = random.choice(['very_short', 'short', 'medium'])
            elif work.design.nail_shape in ['stiletto', 'coffin', 'ballerina']:
                try_on_task.nail_length = random.choice(['long', 'very_long'])
            else:
                try_on_task.nail_length = 'medium'
            analysis_details['nail_length_source'] = f'基于历史作品甲型推断长度'
        else:
            try_on_task.hand_shape = 'standard'
            try_on_task.nail_length = 'medium'

    if try_on_task.customer and not try_on_task.skin_tone:
        works = NailWork.objects.filter(customer=try_on_task.customer)
        if works.exists():
            color_counter = Counter()
            for w in works:
                if w.actual_color:
                    for tone, colors in SKIN_TONE_COLOR_MATCH.items():
                        if any(c in w.actual_color for c in colors):
                            color_counter[tone] += 1
            if color_counter:
                try_on_task.skin_tone = color_counter.most_common(1)[0][0]
                analysis_details['skin_tone_source'] = '基于顾客历史作品色系统计推断'

    if not try_on_task.skin_tone:
        try_on_task.skin_tone = random.choice(skin_tones)
        analysis_details['skin_tone_source'] = '模拟视觉识别默认推断'
    if not try_on_task.hand_shape:
        try_on_task.hand_shape = random.choice(hand_shapes)
        analysis_details['hand_shape_source'] = '模拟视觉识别默认推断'
    if not try_on_task.nail_length:
        try_on_task.nail_length = random.choice(nail_lengths)
        analysis_details['nail_length_source'] = '模拟视觉识别默认推断'

    analysis_details['skin_tone'] = try_on_task.get_skin_tone_display()
    analysis_details['hand_shape'] = try_on_task.get_hand_shape_display()
    analysis_details['nail_length'] = try_on_task.get_nail_length_display()
    analysis_details['confidence'] = round(random.uniform(75, 98), 1)

    try_on_task.analysis_details = analysis_details
    return try_on_task


def calculate_design_similarity(try_on_task, design):
    scores = {}
    breakdown = {}

    scores['shape_score'] = score_design_shape(
        design.nail_shape, try_on_task.hand_shape, try_on_task.nail_length,
        HAND_SHAPE_SHAPE_MATCH, NAIL_LENGTH_SHAPE_MATCH
    )
    shape_weights = HAND_SHAPE_SHAPE_MATCH.get(try_on_task.hand_shape, [])
    length_weights = NAIL_LENGTH_SHAPE_MATCH.get(try_on_task.nail_length, [])
    if design.nail_shape in shape_weights:
        breakdown['shape_hand_match'] = f'适配{try_on_task.get_hand_shape_display()}'
    if design.nail_shape in length_weights:
        breakdown['shape_length_match'] = f'适配{try_on_task.get_nail_length_display()}'

    scores['color_score'] = score_design_color(
        design.color_system, try_on_task.skin_tone, try_on_task.preferred_colors,
        SKIN_TONE_COLOR_MATCH
    )
    tone_colors = SKIN_TONE_COLOR_MATCH.get(try_on_task.skin_tone, [])
    for c in tone_colors:
        if c in design.color_system:
            breakdown['color_tone_match'] = f'{design.color_system} 适配{try_on_task.get_skin_tone_display()}'
            break
    if try_on_task.preferred_colors:
        pref_colors = [c.strip() for c in try_on_task.preferred_colors.split(',') if c.strip()]
        for pc in pref_colors:
            if pc[:1] in design.color_system or pc[:2] in design.color_system:
                breakdown['color_preference_match'] = f'匹配偏好色系：{pc}'
                break

    past_decors = set()
    has_high_satisfaction = False
    if try_on_task.customer:
        works = NailWork.objects.filter(customer=try_on_task.customer)
        for w in works:
            if w.design and w.design.decoration:
                for d in w.design.decoration.split('、'):
                    past_decors.add(d.strip())
        has_high_satisfaction = works.filter(satisfaction__gte=4).exists()

    scores['decoration_score'] = score_design_decoration(design.decoration, past_decors, has_high_satisfaction)
    for pd in past_decors:
        if pd and pd in design.decoration:
            breakdown['deco_history_match'] = f'匹配历史装饰元素：{pd}'
            break
    if has_high_satisfaction and scores['decoration_score'] >= 50:
        breakdown['deco_satisfaction_boost'] = '基于历史满意度加权'

    pref_styles_str = ''
    history_tags = set()
    if try_on_task.customer:
        pref, _ = CustomerPreference.objects.get_or_create(customer=try_on_task.customer)
        pref_styles_str = pref.preferred_styles
        works = NailWork.objects.filter(customer=try_on_task.customer)
        for w in works:
            if w.design:
                for t in w.design.style_tags.all():
                    history_tags.add(t.name)

    design_tags = set(t.name for t in design.style_tags.all())
    scores['style_score'] = score_design_style(design_tags, pref_styles_str, history_tags)
    pref_list = [s.strip() for s in pref_styles_str.split(',') if s.strip()] if pref_styles_str else []
    for ps in pref_list:
        if ps in design_tags:
            breakdown['style_preference_match'] = f'匹配偏好风格：{ps}'
            break
    for ht in history_tags:
        if ht in design_tags:
            breakdown['style_history_match'] = f'匹配历史风格：{ht}'
            break

    scores['occasion_score'] = score_design_occasion(design.occasion, try_on_task.target_occasion)
    if try_on_task.target_occasion:
        if design.occasion == try_on_task.target_occasion:
            breakdown['occasion_exact_match'] = f'匹配目标场合：{design.get_occasion_display()}'
        else:
            related = {
                'party': ['date', 'festival', 'wedding'],
                'wedding': ['party', 'date', 'festival'],
                'date': ['party', 'wedding'],
                'festival': ['party', 'travel'],
                'travel': ['festival', 'daily'],
                'office': ['daily'],
                'daily': ['office', 'travel'],
            }
            if design.occasion in related.get(try_on_task.target_occasion, []):
                breakdown['occasion_related'] = f'相关场合推荐'

    works_with_design = NailWork.objects.filter(design=design)
    avg_sat = works_with_design.aggregate(avg=Avg('satisfaction'))['avg']
    appt_count = Appointment.objects.filter(design=design, status='completed').count()
    scores['satisfaction_score'] = score_design_satisfaction(avg_sat, appt_count)
    if avg_sat:
        breakdown['satisfaction_avg'] = f'平均满意度 {avg_sat:.1f} 星'
    if appt_count > 5:
        breakdown['satisfaction_popular'] = f'热门款式（{appt_count}次预约）'

    scores['budget_score'] = score_design_budget(design.price, try_on_task.budget, BUDGET_RANGES)
    if try_on_task.budget:
        min_price, max_price = BUDGET_RANGES.get(try_on_task.budget, (0, 999999))
        try:
            price = float(design.price)
        except (TypeError, ValueError):
            price = 0
        if min_price <= price <= max_price:
            breakdown['budget_match'] = f'价格 ¥{price} 在预算范围内'
        elif price < min_price:
            breakdown['budget_below'] = f'价格 ¥{price} 低于预算'
        else:
            breakdown['budget_over'] = f'价格 ¥{price} 超出预算，适度降权'

    weights = {
        'shape_score': 0.15,
        'color_score': 0.20,
        'decoration_score': 0.10,
        'style_score': 0.15,
        'occasion_score': 0.15,
        'satisfaction_score': 0.15,
        'budget_score': 0.10,
    }
    scores['similarity_score'] = weighted_score(scores, weights)
    scores['score_breakdown'] = breakdown

    return scores


def generate_similar_recommendations(try_on_task, top_n=12):
    designs = NailDesign.objects.all()
    scored_designs = []

    for design in designs:
        sim = calculate_design_similarity(try_on_task, design)
        scored_designs.append({
            'design': design,
            **sim
        })

    scored_designs.sort(key=lambda x: x['similarity_score'], reverse=True)
    top_designs = scored_designs[:top_n]

    SimilarDesignResult.objects.filter(try_on_task=try_on_task).delete()

    results = []
    for rank, item in enumerate(top_designs, 1):
        result = SimilarDesignResult.objects.create(
            try_on_task=try_on_task,
            design=item['design'],
            similarity_score=item['similarity_score'],
            shape_score=item['shape_score'],
            color_score=item['color_score'],
            decoration_score=item['decoration_score'],
            style_score=item['style_score'],
            occasion_score=item['occasion_score'],
            satisfaction_score=item['satisfaction_score'],
            budget_score=item['budget_score'],
            score_breakdown=item.get('score_breakdown', {}),
            rank=rank,
        )
        results.append(result)

    return results


def process_try_on_task(try_on_task):
    try:
        try_on_task.status = 'processing'
        try_on_task.save()

        analyze_hand_features(try_on_task)

        generate_similar_recommendations(try_on_task)

        try_on_task.status = 'completed'
        try_on_task.completed_at = datetime.now()
        try_on_task.save()

        return True
    except Exception as e:
        try_on_task.status = 'failed'
        try_on_task.error_message = str(e)
        try_on_task.save()
        return False
