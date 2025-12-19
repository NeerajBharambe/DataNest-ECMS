from django.contrib import admin
from .models import Document, Metadata

class MetadataInline(admin.TabularInline):
    model = Metadata
    extra = 1

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'status', 'created_at')
    inlines = [MetadataInline]

admin.site.register(Metadata)
