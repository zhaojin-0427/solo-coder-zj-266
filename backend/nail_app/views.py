from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, Sum, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
import random
from .models import (
    Technician, Customer, StyleTag, NailDesign, Appointment, NailWork,
    CustomerPreference, ContactRecord, RiskScoreHistory, TryOnTask,
    SimilarDesignResult, DesignClickLog
)
from .serializers import (
    TechnicianSerializer, CustomerSerializer, StyleTagSerializer, NailDesignSerializer,
    AppointmentSerializer, NailWorkSerializer, CustomerPreferenceSerializer,
    ContactRecordSerializer, RiskScoreHistorySerializer, TryOnTaskSerializer,
    SimilarDesignResultSerializer, DesignClickLogSerializer
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

    shape_score = 0
    shape_weights = HAND_SHAPE_SHAPE_MATCH.get(try_on_task.hand_shape, [])
    length_weights = NAIL_LENGTH_SHAPE_MATCH.get(try_on_task.nail_length, [])
    if design.nail_shape in shape_weights:
        shape_score += 50
        breakdown['shape_hand_match'] = f'适配{try_on_task.get_hand_shape_display()}'
    if design.nail_shape in length_weights:
        shape_score += 50
        breakdown['shape_length_match'] = f'适配{try_on_task.get_nail_length_display()}'
    scores['shape_score'] = shape_score

    color_score = 0
    tone_colors = SKIN_TONE_COLOR_MATCH.get(try_on_task.skin_tone, [])
    for c in tone_colors:
        if c in design.color_system:
            color_score += 30
            breakdown['color_tone_match'] = f'{design.color_system} 适配{try_on_task.get_skin_tone_display()}'
            break
    if try_on_task.preferred_colors:
        pref_colors = [c.strip() for c in try_on_task.preferred_colors.split(',') if c.strip()]
        for pc in pref_colors:
            if pc[:1] in design.color_system or pc[:2] in design.color_system:
                color_score += 70
                breakdown['color_preference_match'] = f'匹配偏好色系：{pc}'
                break
    scores['color_score'] = min(color_score, 100)

    deco_score = 0
    if try_on_task.customer:
        works = NailWork.objects.filter(customer=try_on_task.customer)
        past_decors = set()
        for w in works:
            if w.design and w.design.decoration:
                for d in w.design.decoration.split('、'):
                    past_decors.add(d.strip())
        for pd in past_decors:
            if pd and pd in design.decoration:
                deco_score += 50
                breakdown['deco_history_match'] = f'匹配历史装饰元素：{pd}'
                break
        if works.filter(satisfaction__gte=4).exists():
            deco_score += 50
            breakdown['deco_satisfaction_boost'] = '基于历史满意度加权'
    scores['decoration_score'] = min(deco_score, 100) if deco_score > 0 else 20

    style_score = 0
    if try_on_task.customer:
        pref, _ = CustomerPreference.objects.get_or_create(customer=try_on_task.customer)
        pref_styles = [s.strip() for s in pref.preferred_styles.split(',') if s.strip()]
        design_tags = set(t.name for t in design.style_tags.all())
        for ps in pref_styles:
            if ps in design_tags:
                style_score += 60
                breakdown['style_preference_match'] = f'匹配偏好风格：{ps}'
                break
        works = NailWork.objects.filter(customer=try_on_task.customer)
        for w in works:
            if w.design:
                for t in w.design.style_tags.all():
                    if t.name in design_tags:
                        style_score += 40
                        breakdown['style_history_match'] = f'匹配历史风格：{t.name}'
                        break
            if style_score >= 100:
                break
    scores['style_score'] = min(style_score, 100) if style_score > 0 else 25

    occasion_score = 0
    if try_on_task.target_occasion:
        if design.occasion == try_on_task.target_occasion:
            occasion_score = 100
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
                occasion_score = 50
                breakdown['occasion_related'] = f'相关场合推荐'
            else:
                occasion_score = 10
    scores['occasion_score'] = occasion_score if try_on_task.target_occasion else 40

    sat_score = 0
    works_with_design = NailWork.objects.filter(design=design)
    if works_with_design.exists():
        avg_sat = works_with_design.aggregate(avg=Avg('satisfaction'))['avg'] or 0
        sat_score = avg_sat * 20
        appt_count = Appointment.objects.filter(design=design, status='completed').count()
        if appt_count > 5:
            sat_score = min(sat_score + 10, 100)
            breakdown['satisfaction_popular'] = f'热门款式（{appt_count}次预约）'
        breakdown['satisfaction_avg'] = f'平均满意度 {avg_sat:.1f} 星'
    else:
        sat_score = 60
    scores['satisfaction_score'] = round(sat_score, 1)

    budget_score = 0
    if try_on_task.budget:
        min_price, max_price = BUDGET_RANGES.get(try_on_task.budget, (0, 999999))
        try:
            price = float(design.price)
        except (TypeError, ValueError):
            price = 0
        if min_price <= price <= max_price:
            budget_score = 100
            breakdown['budget_match'] = f'价格 ¥{price} 在预算范围内'
        elif price < min_price:
            budget_score = 70
            breakdown['budget_below'] = f'价格 ¥{price} 低于预算'
        else:
            budget_score = max(0, 100 - (price - max_price) / 10)
            breakdown['budget_over'] = f'价格 ¥{price} 超出预算，适度降权'
    else:
        budget_score = 80
    scores['budget_score'] = round(budget_score, 1)

    weights = {
        'shape_score': 0.15,
        'color_score': 0.20,
        'decoration_score': 0.10,
        'style_score': 0.15,
        'occasion_score': 0.15,
        'satisfaction_score': 0.15,
        'budget_score': 0.10,
    }
    total = 0
    for k, w in weights.items():
        total += scores.get(k, 0) * w

    scores['similarity_score'] = round(total, 1)
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


class TryOnTaskViewSet(viewsets.ModelViewSet):
    queryset = TryOnTask.objects.all()
    serializer_class = TryOnTaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get('customer')
        status_param = self.request.query_params.get('status')
        sim_min = self.request.query_params.get('sim_min')
        sim_max = self.request.query_params.get('sim_max')
        if customer:
            qs = qs.filter(customer_id=customer)
        if status_param:
            qs = qs.filter(status=status_param)
        if sim_min or sim_max:
            task_ids = SimilarDesignResult.objects.all()
            if sim_min:
                task_ids = task_ids.filter(similarity_score__gte=float(sim_min))
            if sim_max:
                task_ids = task_ids.filter(similarity_score__lte=float(sim_max))
            qs = qs.filter(id__in=task_ids.values_list('try_on_task_id', flat=True))
        return qs

    def perform_create(self, serializer):
        task = serializer.save()
        process_try_on_task(task)

    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        task = self.get_object()
        task.status = 'pending'
        task.error_message = ''
        task.save()
        success = process_try_on_task(task)
        if success:
            return Response(TryOnTaskSerializer(task).data)
        return Response({'error': task.error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        task = self.get_object()
        results = SimilarDesignResult.objects.filter(try_on_task=task).order_by('rank')
        serializer = SimilarDesignResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def log_click(self, request, pk=None):
        task = self.get_object()
        design_id = request.data.get('design_id')
        click_type = request.data.get('click_type', 'view')
        if not design_id:
            return Response({'error': 'design_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            design = NailDesign.objects.get(id=design_id)
        except NailDesign.DoesNotExist:
            return Response({'error': 'design not found'}, status=status.HTTP_404_NOT_FOUND)
        sim_result = SimilarDesignResult.objects.filter(try_on_task=task, design=design).first()
        if sim_result:
            sim_result.is_viewed = True
            sim_result.viewed_at = datetime.now()
            sim_result.save()
        log = DesignClickLog.objects.create(
            try_on_task=task,
            customer=task.customer,
            design=design,
            similar_result=sim_result,
            click_type=click_type,
        )
        return Response(DesignClickLogSerializer(log).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def create_appointment_draft(self, request, pk=None):
        task = self.get_object()
        if not task.customer:
            return Response({'error': '需要关联顾客才能创建预约草稿'}, status=status.HTTP_400_BAD_REQUEST)
        design_id = request.data.get('design_id')
        if not design_id:
            top_result = SimilarDesignResult.objects.filter(try_on_task=task).order_by('rank').first()
            if top_result:
                design_id = top_result.design_id
        try:
            design = NailDesign.objects.get(id=design_id)
        except NailDesign.DoesNotExist:
            return Response({'error': 'design not found'}, status=status.HTTP_404_NOT_FOUND)

        technicians = Technician.objects.filter(is_active=True)
        technician = technicians.first()
        if not technician:
            return Response({'error': '没有可用的美甲师'}, status=status.HTTP_400_BAD_REQUEST)

        next_date = date.today() + timedelta(days=1)
        appt_data = {
            'customer': task.customer.id,
            'technician': technician.id,
            'design': design.id,
            'appointment_date': next_date.isoformat(),
            'appointment_time': '14:00:00',
            'status': 'pending',
            'notes': f'[试甲转化] 来自试甲任务#{task.id}，推荐款式：{design.name}，相似度评分：{SimilarDesignResult.objects.filter(try_on_task=task, design=design).first().similarity_score if SimilarDesignResult.objects.filter(try_on_task=task, design=design).exists() else "N/A"}',
        }
        serializer = AppointmentSerializer(data=appt_data)
        if serializer.is_valid():
            appt = serializer.save()
            task.converted_appointment = appt
            task.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        customer_id = request.query_params.get('customer')
        if not customer_id:
            return Response([])
        tasks = TryOnTask.objects.filter(customer_id=customer_id).order_by('-created_at')
        serializer = TryOnTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class DesignClickLogViewSet(viewsets.ModelViewSet):
    queryset = DesignClickLog.objects.all()
    serializer_class = DesignClickLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get('customer')
        design = self.request.query_params.get('design')
        click_type = self.request.query_params.get('click_type')
        if customer:
            qs = qs.filter(customer_id=customer)
        if design:
            qs = qs.filter(design_id=design)
        if click_type:
            qs = qs.filter(click_type=click_type)
        return qs


class TryOnStatisticsViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'])
    def conversion_overview(self, request):
        months = int(request.query_params.get('months', 6))
        cutoff = datetime.now() - timedelta(days=30 * months)

        total_tasks = TryOnTask.objects.filter(created_at__gte=cutoff).count()
        completed_tasks = TryOnTask.objects.filter(created_at__gte=cutoff, status='completed').count()
        converted_tasks = TryOnTask.objects.filter(
            created_at__gte=cutoff, converted_appointment__isnull=False
        ).count()
        conversion_rate = round((converted_tasks / completed_tasks * 100), 1) if completed_tasks > 0 else 0

        total_clicks = DesignClickLog.objects.filter(clicked_at__gte=cutoff).count()
        book_clicks = DesignClickLog.objects.filter(clicked_at__gte=cutoff, click_type='book').count()

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'converted_tasks': converted_tasks,
            'conversion_rate': conversion_rate,
            'total_clicks': total_clicks,
            'book_clicks': book_clicks,
        })

    @action(detail=False, methods=['get'])
    def conversion_trend(self, request):
        months = int(request.query_params.get('months', 6))
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

        return Response(trend_data)

    @action(detail=False, methods=['get'])
    def similar_design_ranking(self, request):
        months = int(request.query_params.get('months', 3))
        cutoff = datetime.now() - timedelta(days=30 * months)
        limit = int(request.query_params.get('limit', 10))

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
        return Response(ranking[:limit])

    @action(detail=False, methods=['get'])
    def skin_tone_preference(self, request):
        months = int(request.query_params.get('months', 6))
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

        return Response(tone_preference)

    @action(detail=False, methods=['get'])
    def hand_shape_preference(self, request):
        months = int(request.query_params.get('months', 6))
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

        return Response(shape_preference)
