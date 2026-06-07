from rest_framework import serializers
from .models import (
    Technician, Customer, StyleTag, NailDesign, Appointment, NailWork,
    CustomerPreference, ContactRecord, RiskScoreHistory, TryOnTask,
    SimilarDesignResult, DesignClickLog
)


class TechnicianSerializer(serializers.ModelSerializer):
    works_count = serializers.IntegerField(read_only=True, required=False)
    avg_satisfaction = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Technician
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    works_count = serializers.IntegerField(read_only=True, required=False)
    last_visit = serializers.DateField(read_only=True, required=False)
    member_level_display = serializers.CharField(source='get_member_level_display', read_only=True)
    risk_reasons = serializers.JSONField(read_only=True, required=False)

    class Meta:
        model = Customer
        fields = '__all__'


class StyleTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleTag
        fields = '__all__'


class NailDesignSerializer(serializers.ModelSerializer):
    style_tags_data = StyleTagSerializer(source='style_tags', many=True, read_only=True)
    technician_name = serializers.CharField(source='technician.name', read_only=True, default='')

    class Meta:
        model = NailDesign
        fields = '__all__'
        extra_kwargs = {'style_tags': {'required': False}}

    def create(self, validated_data):
        style_tags = validated_data.pop('style_tags', [])
        design = NailDesign.objects.create(**validated_data)
        if style_tags:
            design.style_tags.set(style_tags)
        else:
            design.auto_assign_style_tags()
        return design


class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    technician_name = serializers.CharField(source='technician.name', read_only=True)
    design_name = serializers.CharField(source='design.name', read_only=True, default='')
    design_image = serializers.ImageField(source='design.image', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'


class NailWorkSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    technician_name = serializers.CharField(source='technician.name', read_only=True)
    design_name = serializers.CharField(source='design.name', read_only=True, default='')

    class Meta:
        model = NailWork
        fields = '__all__'


class CustomerPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPreference
        fields = '__all__'


class ContactRecordSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_type_display = serializers.CharField(source='get_contact_type_display', read_only=True)

    class Meta:
        model = ContactRecord
        fields = '__all__'


class RiskScoreHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskScoreHistory
        fields = '__all__'


class SimilarDesignResultSerializer(serializers.ModelSerializer):
    design_data = NailDesignSerializer(source='design', read_only=True)

    class Meta:
        model = SimilarDesignResult
        fields = '__all__'


class TryOnTaskSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    customer_phone = serializers.CharField(source='customer.phone', read_only=True, default='')
    reference_work_name = serializers.CharField(source='reference_work.design.name', read_only=True, default='')
    converted_appointment_id = serializers.IntegerField(source='converted_appointment.id', read_only=True, default=None)
    similar_results = SimilarDesignResultSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    skin_tone_display = serializers.CharField(source='get_skin_tone_display', read_only=True, default='')
    hand_shape_display = serializers.CharField(source='get_hand_shape_display', read_only=True, default='')
    nail_length_display = serializers.CharField(source='get_nail_length_display', read_only=True, default='')
    budget_display = serializers.CharField(source='get_budget_display', read_only=True, default='')
    target_occasion_display = serializers.CharField(source='get_target_occasion_display', read_only=True, default='')

    class Meta:
        model = TryOnTask
        fields = '__all__'


class DesignClickLogSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    design_name = serializers.CharField(source='design.name', read_only=True)
    click_type_display = serializers.CharField(source='get_click_type_display', read_only=True)

    class Meta:
        model = DesignClickLog
        fields = '__all__'
