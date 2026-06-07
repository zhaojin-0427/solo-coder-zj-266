from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, Sum, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
from .models import (
    Technician, Customer, StyleTag, NailDesign, Appointment, NailWork,
    CustomerPreference, ContactRecord, RiskScoreHistory
)
from .serializers import (
    TechnicianSerializer, CustomerSerializer, StyleTagSerializer, NailDesignSerializer,
    AppointmentSerializer, NailWorkSerializer, CustomerPreferenceSerializer,
    ContactRecordSerializer, RiskScoreHistorySerializer
)


class TechnicianViewSet(viewsets.ModelViewSet):
    queryset = Technician.objects.all()
    serializer_class = TechnicianSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            works_count=Count('works'),
            avg_satisfaction=Avg('works__satisfaction')
        )
        return qs


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            works_count=Count('works'),
            last_visit=Max('works__completed_at')
        )
        return qs

    @action(detail=True, methods=['get'])
    def preference(self, request, pk=None):
        customer = self.get_object()
        pref, created = CustomerPreference.objects.get_or_create(customer=customer)
        serializer = CustomerPreferenceSerializer(pref)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'put'])
    def update_preference(self, request, pk=None):
        customer = self.get_object()
        pref, _ = CustomerPreference.objects.get_or_create(customer=customer)
        serializer = CustomerPreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        customer = self.get_object()
        recommendations = get_customer_recommendations(customer)
        return Response(recommendations)

    @action(detail=True, methods=['get'])
    def churn_risk(self, request, pk=None):
        customer = self.get_object()
        result = calculate_churn_risk(customer)
        return Response(result)

    @action(detail=True, methods=['get'])
    def contact_records(self, request, pk=None):
        customer = self.get_object()
        records = ContactRecord.objects.filter(customer=customer)
        serializer = ContactRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def risk_history(self, request, pk=None):
        customer = self.get_object()
        history = RiskScoreHistory.objects.filter(customer=customer).order_by('recorded_at')
        serializer = RiskScoreHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_contact(self, request, pk=None):
        customer = self.get_object()
        data = request.data.copy()
        data['customer'] = customer.id
        serializer = ContactRecordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            customer.last_contact_at = datetime.now()
            customer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def create_followup_appointment(self, request, pk=None):
        customer = self.get_object()
        data = request.data.copy()
        data['customer'] = customer.id
        data['status'] = data.get('status', 'pending')
        data['notes'] = data.get('notes', '') + ' [跟进预约草稿]'
        serializer = AppointmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StyleTagViewSet(viewsets.ModelViewSet):
    queryset = StyleTag.objects.all()
    serializer_class = StyleTagSerializer


class NailDesignViewSet(viewsets.ModelViewSet):
    queryset = NailDesign.objects.all()
    serializer_class = NailDesignSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        shape = self.request.query_params.get('shape')
        occasion = self.request.query_params.get('occasion')
        color = self.request.query_params.get('color')
        tag = self.request.query_params.get('tag')
        search = self.request.query_params.get('search')
        if shape:
            qs = qs.filter(nail_shape=shape)
        if occasion:
            qs = qs.filter(occasion=occasion)
        if color:
            qs = qs.filter(color_system__icontains=color)
        if tag:
            qs = qs.filter(style_tags__name=tag)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(color_system__icontains=search) |
                Q(decoration__icontains=search)
            )
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save()


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        customer = self.request.query_params.get('customer')
        technician = self.request.query_params.get('technician')
        if status_param:
            qs = qs.filter(status=status_param)
        if date_from:
            qs = qs.filter(appointment_date__gte=date_from)
        if date_to:
            qs = qs.filter(appointment_date__lte=date_to)
        if customer:
            qs = qs.filter(customer_id=customer)
        if technician:
            qs = qs.filter(technician_id=technician)
        return qs


class NailWorkViewSet(viewsets.ModelViewSet):
    queryset = NailWork.objects.all()
    serializer_class = NailWorkSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get('customer')
        technician = self.request.query_params.get('technician')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if customer:
            qs = qs.filter(customer_id=customer)
        if technician:
            qs = qs.filter(technician_id=technician)
        if date_from:
            qs = qs.filter(completed_at__gte=date_from)
        if date_to:
            qs = qs.filter(completed_at__lte=date_to)
        return qs


def get_current_season():
    month = datetime.now().month
    if month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'autumn'
    else:
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


def calculate_churn_risk(customer):
    today = date.today()
    factors = {}
    total_score = 0
    max_score = 100
    reasons = []

    works = NailWork.objects.filter(customer=customer).order_by('-completed_at')
    appointments = Appointment.objects.filter(customer=customer)

    last_visit = works.first().completed_at if works.exists() else None
    if last_visit:
        days_since = (today - last_visit).days
        if days_since <= 15:
            visit_score = 5
        elif days_since <= 30:
            visit_score = 15
        elif days_since <= 45:
            visit_score = 25
        elif days_since <= 60:
            visit_score = 35
        elif days_since <= 90:
            visit_score = 45
        else:
            visit_score = 55
        factors['days_since_visit'] = days_since
        if days_since > 45:
            reasons.append(f'已 {days_since} 天未到店')
    else:
        visit_score = 30
        factors['days_since_visit'] = None
        reasons.append('暂无到店记录')
    total_score += visit_score * 0.35

    cancel_count = appointments.filter(status='cancelled').count()
    total_appt = appointments.count()
    cancel_rate = (cancel_count / total_appt * 100) if total_appt > 0 else 0
    if cancel_count == 0:
        cancel_score = 0
    elif cancel_count == 1:
        cancel_score = 15
    elif cancel_count == 2:
        cancel_score = 25
    elif cancel_count <= 4:
        cancel_score = 35
    else:
        cancel_score = 50
    factors['cancel_count'] = cancel_count
    factors['cancel_rate'] = round(cancel_rate, 1)
    if cancel_count >= 2:
        reasons.append(f'累计取消 {cancel_count} 次预约（取消率 {cancel_rate:.0f}%）')
    total_score += cancel_score * 0.2

    if works.count() >= 2:
        recent_works = list(works[:3])
        older_works = list(works[3:6]) if works.count() > 3 else list(works[1:3])
        if recent_works and older_works:
            recent_avg = sum(w.satisfaction for w in recent_works) / len(recent_works)
            older_avg = sum(w.satisfaction for w in older_works) / len(older_works)
            satisfaction_drop = older_avg - recent_avg
            if satisfaction_drop <= 0:
                sat_score = 0
            elif satisfaction_drop <= 0.5:
                sat_score = 15
            elif satisfaction_drop <= 1:
                sat_score = 25
            elif satisfaction_drop <= 1.5:
                sat_score = 40
            else:
                sat_score = 55
            factors['recent_avg_satisfaction'] = round(recent_avg, 2)
            factors['older_avg_satisfaction'] = round(older_avg, 2)
            factors['satisfaction_drop'] = round(satisfaction_drop, 2)
            if satisfaction_drop >= 0.5:
                reasons.append(f'满意度下降 {satisfaction_drop:.1f} 星（{older_avg:.1f} → {recent_avg:.1f}）')
        else:
            sat_score = 0
    else:
        sat_score = 10
        factors['recent_avg_satisfaction'] = None
    total_score += sat_score * 0.2

    if works.count() >= 3:
        try:
            pref, _ = CustomerPreference.objects.get_or_create(customer=customer)
            pref_colors = set(c.strip() for c in pref.preferred_colors.split(',') if c.strip())
            pref_styles = set(s.strip() for s in pref.preferred_styles.split(',') if s.strip())
            recent_works_color = Counter()
            recent_works_style = Counter()
            for w in works[:3]:
                if w.actual_color:
                    recent_works_color[w.actual_color] += 1
                if w.design:
                    for t in w.design.style_tags.all():
                        recent_works_style[t.name] += 1
            color_match = any(c in pref_colors for c in recent_works_color.keys()) if pref_colors else True
            style_match = any(s in pref_styles for s in recent_works_style.keys()) if pref_styles else True
            if not color_match and not style_match:
                pref_score = 40
                reasons.append('近期作品偏好与登记偏好差异较大')
            elif not color_match or not style_match:
                pref_score = 20
            else:
                pref_score = 0
            factors['pref_color_match'] = color_match
            factors['pref_style_match'] = style_match
        except Exception:
            pref_score = 0
    else:
        pref_score = 0
    total_score += pref_score * 0.15

    if works.exists():
        avg_duration = works.aggregate(avg=Avg('duration_days'))['avg'] or 0
        if avg_duration >= 25:
            dur_score = 0
        elif avg_duration >= 20:
            dur_score = 10
        elif avg_duration >= 15:
            dur_score = 20
        elif avg_duration >= 10:
            dur_score = 35
        else:
            dur_score = 50
        factors['avg_duration_days'] = round(avg_duration, 1)
        if avg_duration < 20:
            reasons.append(f'作品平均维持仅 {avg_duration:.0f} 天，低于正常水平')
    else:
        dur_score = 10
    total_score += dur_score * 0.1

    final_score = round(min(total_score, max_score), 1)
    if final_score >= 70:
        risk_level = 'high'
        risk_label = '高风险'
    elif final_score >= 40:
        risk_level = 'medium'
        risk_label = '中风险'
    else:
        risk_level = 'low'
        risk_label = '低风险'

    if final_score >= 70:
        scripts = [
            f'您好 {customer.name}，好久不见啦！最近有适合您的新款式到店，特别适合这个季节，想邀您来体验一下~',
            f'{customer.name}，您上次来已经有段时间啦，我们推出了会员专属优惠，老顾客还可以享受额外福利哦！',
        ]
        action_text = '紧急回访，建议本周内电话或微信联系，提供专属优惠或赠送小礼品'
    elif final_score >= 40:
        scripts = [
            f'{customer.name} 您好，最近天气变化，记得照顾好自己哦~ 我们上新了几款非常适合您风格的款式，有空可以来看看！',
            f'{customer.name}，距离您上次到店有段时间了，想问问您之前做的指甲还满意吗？有任何问题随时可以过来免费修补~',
        ]
        action_text = '建议两周内联系，推送新款资讯和会员活动'
    else:
        scripts = [
            f'{customer.name} 您好，非常感谢您一直以来的支持！最近我们有新款上新，随时欢迎您过来体验~',
        ]
        action_text = '正常维护，可在节日或活动时发送问候'

    customer.churn_risk_score = final_score
    customer.recommended_action = action_text
    customer.save()

    RiskScoreHistory.objects.create(
        customer=customer,
        score=final_score,
        factors={**factors, 'reasons': reasons}
    )

    return {
        'score': final_score,
        'risk_level': risk_level,
        'risk_label': risk_label,
        'reasons': reasons,
        'factors': factors,
        'scripts': scripts,
        'recommended_action': action_text,
    }


def get_high_risk_customers(threshold=40):
    results = []
    for customer in Customer.objects.all():
        risk = calculate_churn_risk(customer)
        if risk['score'] >= threshold:
            cust_data = CustomerSerializer(customer).data
            cust_data['risk_score'] = risk['score']
            cust_data['risk_level'] = risk['risk_level']
            cust_data['risk_label'] = risk['risk_label']
            cust_data['risk_reasons'] = risk['reasons']
            cust_data['scripts'] = risk['scripts']
            cust_data['recommended_action'] = risk['recommended_action']
            results.append(cust_data)
    results.sort(key=lambda x: x['risk_score'], reverse=True)
    return results


class CustomerPreferenceViewSet(viewsets.ModelViewSet):
    queryset = CustomerPreference.objects.all()
    serializer_class = CustomerPreferenceSerializer


class ContactRecordViewSet(viewsets.ModelViewSet):
    queryset = ContactRecord.objects.all()
    serializer_class = ContactRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get('customer')
        if customer:
            qs = qs.filter(customer_id=customer)
        return qs


class CustomerOpsViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        threshold = float(request.query_params.get('threshold', 40))
        results = get_high_risk_customers(threshold)
        return Response(results)

    @action(detail=False, methods=['post'])
    def recalculate_all(self, request):
        updated = 0
        for customer in Customer.objects.all():
            calculate_churn_risk(customer)
            updated += 1
        return Response({'updated': updated})


class StatisticsViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'])
    def color_ranking(self, request):
        months = int(request.query_params.get('months', 6))
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
        return Response(ranking)

    @action(detail=False, methods=['get'])
    def design_lifecycle(self, request):
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
        return Response(result)

    @action(detail=False, methods=['get'])
    def preference_trend(self, request):
        months = int(request.query_params.get('months', 6))
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

        return Response({
            'months': months_list,
            'total_monthly': list(monthly),
            'color_trend': color_data,
            'style_trend': style_data,
        })

    @action(detail=False, methods=['get'])
    def technician_efficiency(self, request):
        months = int(request.query_params.get('months', 3))
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
        return Response(result)

    @action(detail=False, methods=['get'])
    def overview(self, request):
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

        return Response({
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
        })

    @action(detail=False, methods=['get'])
    def member_level_distribution(self, request):
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
        return Response(result)

    @action(detail=False, methods=['get'])
    def repurchase_interval(self, request):
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
            return Response({'avg_interval': 0, 'intervals': [], 'distribution': []})

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

        return Response({
            'avg_interval': avg_interval,
            'intervals': intervals[:100],
            'distribution': [{'label': b['label'], 'count': b['count']} for b in buckets]
        })

    @action(detail=False, methods=['get'])
    def churn_risk_trend(self, request):
        months = int(request.query_params.get('months', 6))
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
            return Response({
                'months': [month_key],
                'trend_data': [
                    {'name': level_labels[lv], 'data': [score_counts[lv]]}
                    for lv in risk_levels
                ]
            })

        months_list = sorted(list(all_months))
        trend_data = []
        for lv in risk_levels:
            trend_data.append({
                'name': level_labels[lv],
                'data': [monthly_data[m][lv] for m in months_list]
            })

        return Response({
            'months': months_list,
            'trend_data': trend_data
        })
