from django.contrib import admin
from .models import Technician, Customer, StyleTag, NailDesign, Appointment, NailWork, CustomerPreference


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'specialty', 'is_active', 'hire_date')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'gender', 'birthday', 'created_at')
    list_filter = ('gender',)
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
