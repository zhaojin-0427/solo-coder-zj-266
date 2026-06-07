from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, Sum, Max
from django.db.models.functions import TruncMonth, TruncWeek
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from .models import Technician, Customer, StyleTag, NailDesign, Appointment, NailWork, CustomerPreference
from .serializers import (
    TechnicianSerializer, CustomerSerializer, StyleTagSerializer, NailDesignSerializer,
    AppointmentSerializer, NailWorkSerializer, CustomerPreferenceSerializer
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


class CustomerPreferenceViewSet(viewsets.ModelViewSet):
    queryset = CustomerPreference.objects.all()
    serializer_class = CustomerPreferenceSerializer


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

        return Response({
            'total_customers': total_customers,
            'total_designs': total_designs,
            'total_works': total_works,
            'pending_appointments': pending_appointments,
            'today_appointments': today_appointments,
            'month_works': month_works,
            'avg_satisfaction': round(avg_satisfaction, 2),
        })
