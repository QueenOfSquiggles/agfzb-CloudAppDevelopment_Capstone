from django.contrib import admin

from djangoapp.models import CarMake, CarModel



# CarModelInline class
class CarModelInline(admin.StackedInline):
  model = CarModel
  extra = 5

# CarModelAdmin class
class CarModelAdmin(admin.ModelAdmin):
  fields=['name', 'dealer_id', 'type', 'year']

# CarMakeAdmin class with CarModelInline
class CarMakeAdmin(admin.ModelAdmin):
  fields=['name', 'description']
  inlines=[CarModelInline]

# Register models here
admin.site.register(CarModel, CarModelAdmin)
admin.site.register(CarMake, CarMakeAdmin)
