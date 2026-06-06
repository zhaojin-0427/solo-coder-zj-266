from rest_framework import serializers
from .models import Technician, Customer, StyleTag, NailDesign, Appointment, NailWork, CustomerPreference


class TechnicianSerializer(serializers.ModelSerializer):
    works_count = serializers.IntegerField(read_only=True, required=False)
    avg_satisfaction = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Technician
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    works_count = serializers.IntegerField(read_only=True, required=False)
    last_visit = serializers.DateField(read_only=True, required=False)

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
