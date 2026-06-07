from django.contrib import admin
from .models import (
    Technician, Customer, StyleTag, NailDesign, Appointment, NailWork,
    CustomerPreference, ContactRecord, RiskScoreHistory, TryOnTask,
    SimilarDesignResult, DesignClickLog
)


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'specialty', 'is_active', 'hire_date')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'gender', 'member_level', 'churn_risk_score', 'birthday', 'created_at')
    list_filter = ('gender', 'member_level')
    search_fields = ('name', 'phone')


@admin.register(StyleTag)
class StyleTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')


@admin.register(NailDesign)
class NailDesignAdmin(admin.ModelAdmin):
    list_display = ('name', 'nail_shape', 'color_system', 'occasion', 'technician', 'price', 'created_at')
    list_filter = ('nail_shape', 'occasion', 'created_at')
    search_fields = ('name', 'color_system', 'decoration')
    filter_horizontal = ('style_tags',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'technician', 'design', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('customer__name', 'technician__name')


@admin.register(NailWork)
class NailWorkAdmin(admin.ModelAdmin):
    list_display = ('customer', 'technician', 'satisfaction', 'duration_days', 'completed_at')
    list_filter = ('satisfaction', 'completed_at')
    search_fields = ('customer__name', 'technician__name')


@admin.register(CustomerPreference)
class CustomerPreferenceAdmin(admin.ModelAdmin):
    list_display = ('customer', 'preferred_colors', 'preferred_styles', 'updated_at')
    search_fields = ('customer__name',)


@admin.register(ContactRecord)
class ContactRecordAdmin(admin.ModelAdmin):
    list_display = ('customer', 'contact_type', 'contacted_at', 'operator')
    list_filter = ('contact_type', 'contacted_at')
    search_fields = ('customer__name', 'content')


@admin.register(RiskScoreHistory)
class RiskScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'score', 'recorded_at')
    list_filter = ('recorded_at',)
    search_fields = ('customer__name',)


@admin.register(TryOnTask)
class TryOnTaskAdmin(admin.ModelAdmin):
    list_display = ('customer', 'status', 'skin_tone', 'hand_shape', 'nail_length', 'target_occasion', 'created_at')
    list_filter = ('status', 'skin_tone', 'hand_shape', 'nail_length', 'target_occasion', 'created_at')
    search_fields = ('customer__name',)
    readonly_fields = ('created_at', 'completed_at')


@admin.register(SimilarDesignResult)
class SimilarDesignResultAdmin(admin.ModelAdmin):
    list_display = ('try_on_task', 'design', 'similarity_score', 'rank', 'is_viewed')
    list_filter = ('is_viewed',)
    search_fields = ('try_on_task__customer__name', 'design__name')


@admin.register(DesignClickLog)
class DesignClickLogAdmin(admin.ModelAdmin):
    list_display = ('customer', 'design', 'click_type', 'clicked_at')
    list_filter = ('click_type', 'clicked_at')
    search_fields = ('customer__name', 'design__name')
