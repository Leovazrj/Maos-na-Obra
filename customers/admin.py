from django.contrib import admin
from .models import Customer, CustomerInteraction, CustomerDocument, CustomerPhoto

class CustomerInteractionInline(admin.TabularInline):
    model = CustomerInteraction
    extra = 1

class CustomerDocumentInline(admin.TabularInline):
    model = CustomerDocument
    extra = 1

class CustomerPhotoInline(admin.TabularInline):
    model = CustomerPhoto
    extra = 1

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'person_type', 'document_number', 'email', 'phone', 'status', 'created_at')
    list_filter = ('person_type', 'status')
    search_fields = ('name', 'document_number', 'email')
    inlines = [CustomerInteractionInline, CustomerDocumentInline, CustomerPhotoInline]

@admin.register(CustomerInteraction)
class CustomerInteractionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'interaction_type', 'interaction_date', 'user')
    list_filter = ('interaction_type', 'interaction_date')
    search_fields = ('customer__name', 'description')

@admin.register(CustomerDocument)
class CustomerDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'visible_in_portal', 'created_at')
    list_filter = ('visible_in_portal', 'created_at')
    search_fields = ('title', 'customer__name')

@admin.register(CustomerPhoto)
class CustomerPhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'visible_in_portal', 'created_at')
    list_filter = ('visible_in_portal', 'created_at')
    search_fields = ('title', 'customer__name')
