from django.contrib import admin
from .models import Transportation, EnergyUsage, WasteData, WaterUsage, UserProfile, CarbonResult

admin.site.register(Transportation)
admin.site.register(EnergyUsage)
admin.site.register(WasteData)
admin.site.register(WaterUsage)
admin.site.register(UserProfile)
admin.site.register(CarbonResult)