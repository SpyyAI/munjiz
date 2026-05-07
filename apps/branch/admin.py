from django.contrib import admin
from .models import Branch, Staff, Counter, Kiosk, DigitalScreen


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_id', 'name_ar', 'city', 'counters_total', 'kiosks_total', 'is_active')
    search_fields = ('branch_id', 'name_ar')


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name_ar', 'role', 'counter', 'status', 'performance_score')
    list_filter = ('role', 'status', 'branch')
    search_fields = ('employee_id', 'name_ar')


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('number', 'branch', 'counter_type', 'is_active', 'assigned_staff')
    list_filter = ('counter_type', 'is_active')


@admin.register(Kiosk)
class KioskAdmin(admin.ModelAdmin):
    list_display = ('kiosk_id', 'location_ar', 'status', 'usage_today')
    list_filter = ('status',)


@admin.register(DigitalScreen)
class DigitalScreenAdmin(admin.ModelAdmin):
    list_display = ('screen_id', 'location_ar', 'current_content', 'is_active')
