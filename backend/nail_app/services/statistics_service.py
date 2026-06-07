from datetime import datetime, timedelta
from collections import Counter, defaultdict
from django.db.models import Count, Avg, Q, Sum
from django.db.models.functions import TruncMonth
from ..models import (
    Customer, NailDesign, NailWork, Appointment, Technician,
    RiskScoreHistory, TryOnTask, SimilarDesignResult, DesignClickLog
)


def get_color_ranking(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)
    works = NailWork.objects.filter(completed_at__gte=cutoff)
    design_colors = NailDesign.objects.filter(created_at__gte=cutoff)

    colors = []
    for w in works:
        if w.actual_color:
            colors.append(w.actual_color)
    for d in design_colors:
        colors.append(d.color_system)

    counter = Counter(colors)
    ranking = [{'color': k, 'count': v} for k, v in counter.most_common(20) if k]
    return ranking


def get_design_lifecycle():
    designs = NailDesign.objects.annotate(
        appt_count=Count('appointments', filter=Q(appointments__status='completed'))
    ).order_by('-created_at')[:50]

    result = []
    for d in designs:
        avg_duration = NailWork.objects.filter(design=d).aggregate(
            avg=Avg('duration_days')
        )['avg'] or 0
        avg_satisfaction = NailWork.objects.filter(design=d).aggregate(
            avg=Avg('satisfaction')
        )['avg'] or 0
        result.append({
            'id': d.id,
            'name': d.name,
            'image': d.image.url if d.image else '',
            'created_at': d.created_at,
            'appt_count': d.appt_count,
            'avg_duration': round(avg_duration, 1),
            'avg_satisfaction': round(avg_satisfaction, 2),
        })
    return result


def get_preference_trend(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)

    monthly = NailWork.objects.filter(completed_at__gte=cutoff).annotate(
        month=TruncMonth('completed_at')
    ).values('month').annotate(count=Count('id')).order_by('month')

    color_trend = defaultdict(lambda: defaultdict(int))
    style_trend = defaultdict(lambda: defaultdict(int))

    for w in NailWork.objects.filter(completed_at__gte=cutoff):
        month_key = w.completed_at.strftime('%Y-%m')
        if w.actual_color:
            color_trend[month_key][w.actual_color] += 1
        if w.design:
            for tag in w.design.style_tags.all():
                style_trend[month_key][tag.name] += 1

    months_list = sorted(list(set(list(color_trend.keys()) + list(style_trend.keys()))))

    top_colors = Counter()
    for m in color_trend.values():
        top_colors.update(m)
    top_5_colors = [c for c, _ in top_colors.most_common(5)]

    top_styles = Counter()
    for m in style_trend.values():
        top_styles.update(m)
    top_5_styles = [s for s, _ in top_styles.most_common(5)]

    color_data = []
    for color in top_5_colors:
        color_data.append({
            'name': color,
            'data': [color_trend[m].get(color, 0) for m in months_list]
        })

    style_data = []
    for style in top_5_styles:
        style_data.append({
            'name': style,
            'data': [style_trend[m].get(style, 0) for m in months_list]
        })

    return {
        'months': months_list,
        'total_monthly': list(monthly),
        'color_trend': color_data,
        'style_trend': style_data,
    }


def get_technician_efficiency(months=3):
    cutoff = datetime.now() - timedelta(days=30 * months)

    techs = Technician.objects.filter(is_active=True).annotate(
        works_count=Count('works', filter=Q(works__completed_at__gte=cutoff)),
        avg_satisfaction=Avg('works__satisfaction', filter=Q(works__completed_at__gte=cutoff)),
        avg_duration=Avg('works__duration_days', filter=Q(works__completed_at__gte=cutoff)),
    )

    result = []
    for t in techs:
        appt_count = Appointment.objects.filter(
            technician=t, appointment_date__gte=cutoff, status='completed'
        ).count()
        result.append({
            'id': t.id,
            'name': t.name,
            'works_count': t.works_count or 0,
            'appointments_count': appt_count,
            'avg_satisfaction': round(t.avg_satisfaction or 0, 2),
            'avg_duration': round(t.avg_duration or 0, 1),
        })
    result.sort(key=lambda x: x['works_count'], reverse=True)
    return result


def get_overview_stats():
    today = datetime.now().date()
    month_start = today.replace(day=1)
    total_customers = Customer.objects.count()
    total_designs = NailDesign.objects.count()
    total_works = NailWork.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    month_works = NailWork.objects.filter(completed_at__gte=month_start).count()
    avg_satisfaction = NailWork.objects.filter(completed_at__gte=month_start).aggregate(
        avg=Avg('satisfaction')
    )['avg'] or 0

    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    for c in Customer.objects.all():
        if c.churn_risk_score >= 70:
            high_risk_count += 1
        elif c.churn_risk_score >= 40:
            medium_risk_count += 1
        else:
            low_risk_count += 1

    return {
        'total_customers': total_customers,
        'total_designs': total_designs,
        'total_works': total_works,
        'pending_appointments': pending_appointments,
        'today_appointments': today_appointments,
        'month_works': month_works,
        'avg_satisfaction': round(avg_satisfaction, 2),
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
    }


def get_member_level_distribution():
    levels = Customer.objects.values('member_level').annotate(count=Count('id'))
    level_map = {
        'normal': '普通会员',
        'silver': '银卡会员',
        'gold': '金卡会员',
        'platinum': '钻石会员',
    }
    result = []
    for item in levels:
        result.append({
            'level': item['member_level'],
            'level_name': level_map.get(item['member_level'], item['member_level']),
            'count': item['count']
        })
    for lv, name in level_map.items():
        if not any(r['level'] == lv for r in result):
            result.append({'level': lv, 'level_name': name, 'count': 0})
    result.sort(key=lambda x: ['normal', 'silver', 'gold', 'platinum'].index(x['level']))
    return result


def get_repurchase_interval():
    customers_works = Customer.objects.annotate(
        works_count=Count('works')
    ).filter(works_count__gte=2)

    intervals = []
    for customer in customers_works:
        works = NailWork.objects.filter(customer=customer).order_by('completed_at')
        dates = [w.completed_at for w in works]
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i - 1]).days
            intervals.append(interval)

    if not intervals:
        return {'avg_interval': 0, 'intervals': [], 'distribution': []}

    avg_interval = round(sum(intervals) / len(intervals), 1)

    buckets = [
        {'label': '< 20天', 'min': 0, 'max': 20, 'count': 0},
        {'label': '20-30天', 'min': 20, 'max': 30, 'count': 0},
        {'label': '30-45天', 'min': 30, 'max': 45, 'count': 0},
        {'label': '45-60天', 'min': 45, 'max': 60, 'count': 0},
        {'label': '> 60天', 'min': 60, 'max': 9999, 'count': 0},
    ]
    for iv in intervals:
        for b in buckets:
            if b['min'] <= iv < b['max']:
                b['count'] += 1
                break

    return {
        'avg_interval': avg_interval,
        'intervals': intervals[:100],
        'distribution': [{'label': b['label'], 'count': b['count']} for b in buckets]
    }


def get_churn_risk_trend(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)

    risk_levels = ['low', 'medium', 'high']
    level_labels = {'low': '低风险', 'medium': '中风险', 'high': '高风险'}

    monthly_data = defaultdict(lambda: defaultdict(int))
    all_months = set()

    for history in RiskScoreHistory.objects.filter(recorded_at__gte=cutoff):
        month_key = history.recorded_at.strftime('%Y-%m')
        all_months.add(month_key)
        if history.score >= 70:
            monthly_data[month_key]['high'] += 1
        elif history.score >= 40:
            monthly_data[month_key]['medium'] += 1
        else:
            monthly_data[month_key]['low'] += 1

    if not all_months:
        current_month = datetime.now().replace(day=1)
        score_counts = {'low': 0, 'medium': 0, 'high': 0}
        for c in Customer.objects.all():
            if c.churn_risk_score >= 70:
                score_counts['high'] += 1
            elif c.churn_risk_score >= 40:
                score_counts['medium'] += 1
            else:
                score_counts['low'] += 1
        month_key = current_month.strftime('%Y-%m')
        return {
            'months': [month_key],
            'trend_data': [
                {'name': level_labels[lv], 'data': [score_counts[lv]]}
                for lv in risk_levels
            ]
        }

    months_list = sorted(list(all_months))
    trend_data = []
    for lv in risk_levels:
        trend_data.append({
            'name': level_labels[lv],
            'data': [monthly_data[m][lv] for m in months_list]
        })

    return {
        'months': months_list,
        'trend_data': trend_data
    }


def get_tryon_conversion_overview(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)

    total_tasks = TryOnTask.objects.filter(created_at__gte=cutoff).count()
    completed_tasks = TryOnTask.objects.filter(created_at__gte=cutoff, status='completed').count()
    converted_tasks = TryOnTask.objects.filter(
        created_at__gte=cutoff, converted_appointment__isnull=False
    ).count()
    conversion_rate = round((converted_tasks / completed_tasks * 100), 1) if completed_tasks > 0 else 0

    total_clicks = DesignClickLog.objects.filter(clicked_at__gte=cutoff).count()
    book_clicks = DesignClickLog.objects.filter(clicked_at__gte=cutoff, click_type='book').count()

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'converted_tasks': converted_tasks,
        'conversion_rate': conversion_rate,
        'total_clicks': total_clicks,
        'book_clicks': book_clicks,
    }


def get_tryon_conversion_trend(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)

    monthly = defaultdict(lambda: {'tasks': 0, 'converted': 0, 'clicks': 0})
    for task in TryOnTask.objects.filter(created_at__gte=cutoff):
        m = task.created_at.strftime('%Y-%m')
        monthly[m]['tasks'] += 1
        if task.converted_appointment:
            monthly[m]['converted'] += 1
    for log in DesignClickLog.objects.filter(clicked_at__gte=cutoff):
        m = log.clicked_at.strftime('%Y-%m')
        monthly[m]['clicks'] += 1

    months_list = sorted(monthly.keys())
    trend_data = []
    for m in months_list:
        d = monthly[m]
        rate = round(d['converted'] / d['tasks'] * 100, 1) if d['tasks'] > 0 else 0
        trend_data.append({
            'month': m,
            'tasks': d['tasks'],
            'converted': d['converted'],
            'clicks': d['clicks'],
            'conversion_rate': rate,
        })

    return trend_data


def get_similar_design_ranking(months=3, limit=10):
    cutoff = datetime.now() - timedelta(days=30 * months)

    sim_results = SimilarDesignResult.objects.filter(
        try_on_task__created_at__gte=cutoff,
        try_on_task__status='completed'
    )
    design_stats = defaultdict(lambda: {
        'total_score': 0, 'appear_count': 0, 'view_count': 0, 'click_count': 0, 'book_count': 0
    })
    for sr in sim_results:
        ds = design_stats[sr.design_id]
        ds['total_score'] += sr.similarity_score
        ds['appear_count'] += 1
        if sr.is_viewed:
            ds['view_count'] += 1

    click_logs = DesignClickLog.objects.filter(
        clicked_at__gte=cutoff, similar_result__isnull=False
    )
    for log in click_logs:
        if log.design_id in design_stats:
            design_stats[log.design_id]['click_count'] += 1
            if log.click_type == 'book':
                design_stats[log.design_id]['book_count'] += 1

    ranking = []
    for design_id, stats in design_stats.items():
        try:
            design = NailDesign.objects.get(id=design_id)
            avg_score = round(stats['total_score'] / stats['appear_count'], 1) if stats['appear_count'] > 0 else 0
            ranking.append({
                'design_id': design_id,
                'design_name': design.name,
                'design_image': design.image.url if design.image else '',
                'avg_similarity': avg_score,
                'appear_count': stats['appear_count'],
                'view_count': stats['view_count'],
                'click_count': stats['click_count'],
                'book_count': stats['book_count'],
                'composite_score': round(
                    avg_score * 0.4 + stats['view_count'] * 0.25 + stats['click_count'] * 0.2 + stats['book_count'] * 0.15,
                    1
                ),
            })
        except NailDesign.DoesNotExist:
            continue

    ranking.sort(key=lambda x: x['composite_score'], reverse=True)
    return ranking[:limit]


def get_skin_tone_preference(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)

    tone_dist = TryOnTask.objects.filter(
        created_at__gte=cutoff, status='completed'
    ).values('skin_tone').annotate(count=Count('id'))
    tone_labels = dict(TryOnTask.SKIN_TONE_CHOICES)

    tone_preference = []
    for item in tone_dist:
        tone_name = tone_labels.get(item['skin_tone'], item['skin_tone'])
        tone_ids = TryOnTask.objects.filter(
            created_at__gte=cutoff, skin_tone=item['skin_tone']
        ).values_list('id', flat=True)
        sim_results = SimilarDesignResult.objects.filter(
            try_on_task_id__in=tone_ids, rank__lte=3
        ).select_related('design')
        color_counter = Counter()
        for sr in sim_results:
            color_counter[sr.design.color_system] += 1
        top_colors = [{'color': c, 'count': n} for c, n in color_counter.most_common(5)]
        tone_preference.append({
            'skin_tone': item['skin_tone'],
            'skin_tone_name': tone_name,
            'count': item['count'],
            'top_colors': top_colors,
        })

    return tone_preference


def get_hand_shape_preference(months=6):
    cutoff = datetime.now() - timedelta(days=30 * months)

    shape_dist = TryOnTask.objects.filter(
        created_at__gte=cutoff, status='completed'
    ).values('hand_shape').annotate(count=Count('id'))
    shape_labels = dict(TryOnTask.HAND_SHAPE_CHOICES)

    shape_preference = []
    for item in shape_dist:
        shape_name = shape_labels.get(item['hand_shape'], item['hand_shape'])
        shape_ids = TryOnTask.objects.filter(
            created_at__gte=cutoff, hand_shape=item['hand_shape']
        ).values_list('id', flat=True)
        sim_results = SimilarDesignResult.objects.filter(
            try_on_task_id__in=shape_ids, rank__lte=3
        ).select_related('design')
        shape_counter = Counter()
        for sr in sim_results:
            shape_counter[sr.design.get_nail_shape_display()] += 1
        top_shapes = [{'shape': s, 'count': n} for s, n in shape_counter.most_common(5)]
        shape_preference.append({
            'hand_shape': item['hand_shape'],
            'hand_shape_name': shape_name,
            'count': item['count'],
            'top_shapes': top_shapes,
        })

    return shape_preference
