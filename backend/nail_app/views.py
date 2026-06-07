from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, Max
from datetime import datetime, timedelta, date
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
from .services import (
    calculate_churn_risk, get_high_risk_customers,
    get_customer_recommendations,
    analyze_hand_features, calculate_design_similarity,
    generate_similar_recommendations, process_try_on_task,
    get_color_ranking, get_design_lifecycle, get_preference_trend,
    get_technician_efficiency, get_overview_stats, get_member_level_distribution,
    get_repurchase_interval, get_churn_risk_trend, get_tryon_conversion_overview,
    get_tryon_conversion_trend, get_similar_design_ranking, get_skin_tone_preference,
    get_hand_shape_preference
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
        return Response(get_color_ranking(months))

    @action(detail=False, methods=['get'])
    def design_lifecycle(self, request):
        return Response(get_design_lifecycle())

    @action(detail=False, methods=['get'])
    def preference_trend(self, request):
        months = int(request.query_params.get('months', 6))
        return Response(get_preference_trend(months))

    @action(detail=False, methods=['get'])
    def technician_efficiency(self, request):
        months = int(request.query_params.get('months', 3))
        return Response(get_technician_efficiency(months))

    @action(detail=False, methods=['get'])
    def overview(self, request):
        return Response(get_overview_stats())

    @action(detail=False, methods=['get'])
    def member_level_distribution(self, request):
        return Response(get_member_level_distribution())

    @action(detail=False, methods=['get'])
    def repurchase_interval(self, request):
        return Response(get_repurchase_interval())

    @action(detail=False, methods=['get'])
    def churn_risk_trend(self, request):
        months = int(request.query_params.get('months', 6))
        return Response(get_churn_risk_trend(months))


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
        sim_obj = SimilarDesignResult.objects.filter(try_on_task=task, design=design)
        sim_score = sim_obj.first().similarity_score if sim_obj.exists() else "N/A"
        appt_data = {
            'customer': task.customer.id,
            'technician': technician.id,
            'design': design.id,
            'appointment_date': next_date.isoformat(),
            'appointment_time': '14:00:00',
            'status': 'pending',
            'notes': f'[试甲转化] 来自试甲任务#{task.id}，推荐款式：{design.name}，相似度评分：{sim_score}',
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
        return Response(get_tryon_conversion_overview(months))

    @action(detail=False, methods=['get'])
    def conversion_trend(self, request):
        months = int(request.query_params.get('months', 6))
        return Response(get_tryon_conversion_trend(months))

    @action(detail=False, methods=['get'])
    def similar_design_ranking(self, request):
        months = int(request.query_params.get('months', 3))
        limit = int(request.query_params.get('limit', 10))
        return Response(get_similar_design_ranking(months, limit))

    @action(detail=False, methods=['get'])
    def skin_tone_preference(self, request):
        months = int(request.query_params.get('months', 6))
        return Response(get_skin_tone_preference(months))

    @action(detail=False, methods=['get'])
    def hand_shape_preference(self, request):
        months = int(request.query_params.get('months', 6))
        return Response(get_hand_shape_preference(months))
