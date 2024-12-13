from django.contrib import admin
from .models import *

class ClassAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name_plural = "Classes"

class AssignmentAdmin(admin.ModelAdmin):
    actions = ['duplicate_assignment']

    def duplicate_assignment(self, request, queryset):
        for assignment in queryset:
            # Get count of assignments with similar names
            base_name = assignment.name.split(" (#")[0]  # Remove any existing numbering
            existing_count = Assignment.objects.filter(
                name__startswith=base_name,
                class_obj=assignment.class_obj
            ).count()
            
            assignment.pk = None
            assignment.name = f"{base_name} (#{existing_count + 1})"
            assignment.save()
    duplicate_assignment.short_description = "Duplicate selected assignments"

admin.site.register(Class, ClassAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Exam)
