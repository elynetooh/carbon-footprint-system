from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    DEPARTMENT_CHOICES = [
        ('field_operations', '🚛 Field Operations'),
        ('processing_plant', '🏭 Processing Plant'),
        ('water_sanitation', '💧 Water & Sanitation'),
        ('waste_management', '♻️ Waste Management'),
        ('manager', '👨‍💼 Sanergy Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='field_operations')

    def __str__(self):
        return f"{self.user.username} - {self.department}"

class Transportation(models.Model):
    MODE_CHOICES = [
        ('truck', 'Company Truck'),
        ('car', 'Company Car'),
        ('boda', 'Boda Boda'),
        ('matatu', 'Matatu / Bus'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    distance_km = models.FloatField()
    date = models.DateField()

    def co2_kg(self):
        factors = {'truck': 0.27, 'car': 0.12, 'boda': 0.03, 'matatu': 0.05}
        return self.distance_km * factors.get(self.mode, 0)

    def __str__(self):
        return f"{self.user.username} - {self.mode} - {self.date}"

class EnergyUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kwh = models.FloatField()
    date = models.DateField()

    def co2_kg(self):
        return self.kwh * 0.4

    def __str__(self):
        return f"{self.user.username} - {self.kwh}kWh - {self.date}"

class WasteData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight_kg = models.FloatField()
    date = models.DateField()

    def co2_kg(self):
        return self.weight_kg * 0.7

    def __str__(self):
        return f"{self.user.username} - {self.weight_kg}kg - {self.date}"

class WaterUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    liters = models.FloatField()
    date = models.DateField()

    def co2_kg(self):
        return self.liters * 0.0003

    def __str__(self):
        return f"{self.user.username} - {self.liters}L - {self.date}"

class CarbonResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transport_co2 = models.FloatField(default=0)
    energy_co2 = models.FloatField(default=0)
    waste_co2 = models.FloatField(default=0)
    water_co2 = models.FloatField(default=0)
    total_co2 = models.FloatField(default=0)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.total_co2}kg - {self.date}"