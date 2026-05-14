from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Transportation, EnergyUsage, WasteData, WaterUsage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from django.core.mail import send_mail
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import date
from django.utils import timezone
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    user = request.user
    try:
        profile = user.userprofile
        department = profile.department
    except:
        if user.is_staff:
            department = 'kcic_admin'
        else:
            department = 'manager'

    if user.is_staff:
        return redirect('admin_dashboard')
    if department == 'manager':
        return redirect('manager_dashboard')

    current_month = timezone.now().month
    current_year = timezone.now().year

    transports = Transportation.objects.filter(user=user, date__month=current_month, date__year=current_year)
    energies = EnergyUsage.objects.filter(user=user, date__month=current_month, date__year=current_year)
    wastes = WasteData.objects.filter(user=user, date__month=current_month, date__year=current_year)
    waters = WaterUsage.objects.filter(user=user, date__month=current_month, date__year=current_year)

    transport_co2 = sum([t.co2_kg() for t in transports])
    energy_co2 = sum([e.co2_kg() for e in energies])
    waste_co2 = sum([w.co2_kg() for w in wastes])
    water_co2 = sum([w.co2_kg() for w in waters])
    total_co2 = transport_co2 + energy_co2 + waste_co2 + water_co2

    not_submitted = False
    if department == 'field_operations' and transport_co2 == 0:
        not_submitted = True
    elif department == 'processing_plant' and energy_co2 == 0:
        not_submitted = True
    elif department == 'water_sanitation' and water_co2 == 0:
        not_submitted = True
    elif department == 'waste_management' and waste_co2 == 0:
        not_submitted = True

    monthly_data = []
    monthly_labels = []
    for i in range(5, -1, -1):
        month = (current_month - i - 1) % 12 + 1
        year = current_year if current_month - i > 0 else current_year - 1
        month_name = date(year, month, 1).strftime('%b %Y')
        monthly_labels.append(month_name)
        t = sum([x.co2_kg() for x in Transportation.objects.filter(user=user, date__month=month, date__year=year)])
        e = sum([x.co2_kg() for x in EnergyUsage.objects.filter(user=user, date__month=month, date__year=year)])
        w = sum([x.co2_kg() for x in WasteData.objects.filter(user=user, date__month=month, date__year=year)])
        wa = sum([x.co2_kg() for x in WaterUsage.objects.filter(user=user, date__month=month, date__year=year)])
        monthly_data.append(round(t + e + w + wa, 2))

    if len(monthly_data) >= 2 and monthly_data[-2] != 0:
        trend = monthly_data[-1] - monthly_data[-2]
        prediction = round(monthly_data[-1] + trend, 2)
    elif monthly_data[-1] != 0:
        prediction = monthly_data[-1]
    else:
        prediction = 0

    recommendations = []
    if department == 'field_operations':
        if transport_co2 == 0:
            recommendations.append("🚛 No transport data yet. Start logging your fleet trips today!")
        elif transport_co2 <= 10:
            recommendations.append("✅ Great job! Your transport emissions are low. Keep optimizing routes.")
        elif transport_co2 <= 30:
            recommendations.append("🚛 Plan delivery routes efficiently to reduce fuel consumption.")
            recommendations.append("⛽ Consider switching to fuel efficient trucks to cut emissions.")
        else:
            recommendations.append("⚠️ High transport emissions! Review fleet usage urgently.")
            recommendations.append("🚛 Consolidate trips — avoid sending half empty trucks.")
            recommendations.append("⛽ Consider hybrid or electric vehicles for short routes.")

    elif department == 'processing_plant':
        if energy_co2 == 0:
            recommendations.append("⚡ No energy data yet. Start logging your plant energy usage today!")
        elif energy_co2 <= 20:
            recommendations.append("✅ Energy usage is moderate. Keep machines well maintained.")
        elif energy_co2 <= 50:
            recommendations.append("💡 Switch off machines when idle to save energy.")
            recommendations.append("⚡ Schedule high energy tasks during off peak hours.")
        else:
            recommendations.append("⚠️ Very high energy usage! Consider an energy audit.")
            recommendations.append("💡 Replace old equipment with energy efficient alternatives.")
            recommendations.append("🔌 Install solar panels to offset plant energy consumption.")

    elif department == 'water_sanitation':
        if water_co2 == 0:
            recommendations.append("💧 No water data yet. Start logging your water usage today!")
        elif water_co2 <= 5:
            recommendations.append("✅ Water usage is well managed. Keep it up!")
        elif water_co2 <= 15:
            recommendations.append("💧 Fix any leaking pipes to reduce water wastage.")
            recommendations.append("🚿 Encourage staff to use water responsibly.")
        else:
            recommendations.append("⚠️ High water usage! Check for leaks in the system.")
            recommendations.append("💧 Install water recycling systems to reuse grey water.")
            recommendations.append("🌊 Consider rainwater harvesting for non drinking uses.")

    elif department == 'waste_management':
        if waste_co2 == 0:
            recommendations.append("♻️ No waste data yet. Start logging your waste today!")
        elif waste_co2 <= 10:
            recommendations.append("✅ Waste levels are low. Keep up the recycling efforts!")
        elif waste_co2 <= 30:
            recommendations.append("♻️ Increase recycling rates to reduce landfill waste.")
            recommendations.append("🗑️ Separate organic waste for composting.")
        else:
            recommendations.append("⚠️ Very high waste levels! Review waste management process.")
            recommendations.append("♻️ Partner with recycling firms to divert waste from landfill.")
            recommendations.append("🌱 Start a composting program for organic waste.")

    if total_co2 == 0:
        carbon_score = 'N/A'
        score_color = 'gray'
    elif total_co2 <= 5:
        carbon_score = 'A'
        score_color = '#2e7d32'
    elif total_co2 <= 15:
        carbon_score = 'B'
        score_color = '#66bb6a'
    elif total_co2 <= 30:
        carbon_score = 'C'
        score_color = '#ff9800'
    else:
        carbon_score = 'D'
        score_color = '#c62828'

    context = {
        'hide_navbar': True,                          # ← ADDED: hides old top navbar
        'transport_co2': round(transport_co2, 2),
        'energy_co2': round(energy_co2, 2),
        'waste_co2': round(waste_co2, 2),
        'water_co2': round(water_co2, 2),
        'total_co2': round(total_co2, 2),
        'recommendations': recommendations,
        'carbon_score': carbon_score,
        'score_color': score_color,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'current_month': date(current_year, current_month, 1).strftime('%B %Y'),
        'department': department,
        'not_submitted': not_submitted,
        'prediction': prediction,
    }
    return render(request, 'footprint/dashboard.html', context)


@login_required
def add_transport(request):
    if request.method == 'POST':
        mode = request.POST['mode']
        distance = float(request.POST['distance'])
        date_input = request.POST['date']
        obj = Transportation.objects.create(user=request.user, mode=mode, distance_km=distance, date=date_input)
        co2 = round(obj.co2_kg(), 2)
        try:
            send_mail(
                subject='✅ Transport Data Submitted — KCIC Carbon Tracker',
                message=f'''Hello {request.user.username},

Your transport data has been submitted successfully!

Mode: {mode}
Distance: {distance} km
CO2 Emitted: {co2} kg
Date: {date_input}

Thank you for keeping Sanergy carbon data up to date.

KCIC Carbon Tracker''',
                from_email='KCIC Carbon Tracker <sanergy7@gmail.com>',
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except:
            pass
        return redirect('dashboard')
    return render(request, 'footprint/add_transport.html')


@login_required
def add_energy(request):
    if request.method == 'POST':
        kwh = float(request.POST['kwh'])
        date_input = request.POST['date']
        obj = EnergyUsage.objects.create(user=request.user, kwh=kwh, date=date_input)
        co2 = round(obj.co2_kg(), 2)
        try:
            send_mail(
                subject='✅ Energy Data Submitted — KCIC Carbon Tracker',
                message=f'''Hello {request.user.username},

Your energy data has been submitted successfully!

Energy Used: {kwh} kWh
CO2 Emitted: {co2} kg
Date: {date_input}

Thank you for keeping Sanergy carbon data up to date.

KCIC Carbon Tracker''',
                from_email='KCIC Carbon Tracker <sanergy7@gmail.com>',
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except:
            pass
        return redirect('dashboard')
    return render(request, 'footprint/add_energy.html')


@login_required
def add_waste(request):
    if request.method == 'POST':
        weight = float(request.POST['weight'])
        date_input = request.POST['date']
        obj = WasteData.objects.create(user=request.user, weight_kg=weight, date=date_input)
        co2 = round(obj.co2_kg(), 2)
        try:
            send_mail(
                subject='✅ Waste Data Submitted — KCIC Carbon Tracker',
                message=f'''Hello {request.user.username},

Your waste data has been submitted successfully!

Waste Weight: {weight} kg
CO2 Emitted: {co2} kg
Date: {date_input}

Thank you for keeping Sanergy carbon data up to date.

KCIC Carbon Tracker''',
                from_email='KCIC Carbon Tracker <sanergy7@gmail.com>',
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except:
            pass
        return redirect('dashboard')
    return render(request, 'footprint/add_waste.html')


@login_required
def add_water(request):
    if request.method == 'POST':
        liters = float(request.POST['liters'])
        date_input = request.POST['date']
        obj = WaterUsage.objects.create(user=request.user, liters=liters, date=date_input)
        co2 = round(obj.co2_kg(), 2)
        try:
            send_mail(
                subject='✅ Water Data Submitted — KCIC Carbon Tracker',
                message=f'''Hello {request.user.username},

Your water data has been submitted successfully!

Water Used: {liters} liters
CO2 Emitted: {co2} kg
Date: {date_input}

Thank you for keeping Sanergy carbon data up to date.

KCIC Carbon Tracker''',
                from_email='KCIC Carbon Tracker <sanergy7@gmail.com>',
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except:
            pass
        return redirect('dashboard')
    return render(request, 'footprint/add_water.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            department = request.POST.get('department', 'field_operations')
            from .models import UserProfile
            UserProfile.objects.create(user=user, department=department)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'footprint/register.html', {'form': form})


@login_required
def download_pdf(request):
    user = request.user
    current_month = timezone.now().month
    current_year = timezone.now().year

    try:
        profile = user.userprofile
        department = profile.department
    except:
        department = 'kcic_admin' if user.is_staff else 'unknown'

    from .models import UserProfile

    if department == 'manager' or user.is_staff:
        # Aggregate all departments
        profiles = UserProfile.objects.exclude(department='manager')
        transport_co2 = energy_co2 = waste_co2 = water_co2 = 0
        for p in profiles:
            u = p.user
            transport_co2 += sum([x.co2_kg() for x in Transportation.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            energy_co2 += sum([x.co2_kg() for x in EnergyUsage.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            waste_co2 += sum([x.co2_kg() for x in WasteData.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            water_co2 += sum([x.co2_kg() for x in WaterUsage.objects.filter(user=u, date__month=current_month, date__year=current_year)])
        transport_co2 = round(transport_co2, 2)
        energy_co2 = round(energy_co2, 2)
        waste_co2 = round(waste_co2, 2)
        water_co2 = round(water_co2, 2)
        report_title = "Sanergy Kenya — Company Carbon Report"
        report_name = "sanergy_company"
    else:
        # Individual employee data
        transports = Transportation.objects.filter(user=user, date__month=current_month, date__year=current_year)
        energies = EnergyUsage.objects.filter(user=user, date__month=current_month, date__year=current_year)
        wastes = WasteData.objects.filter(user=user, date__month=current_month, date__year=current_year)
        waters = WaterUsage.objects.filter(user=user, date__month=current_month, date__year=current_year)
        transport_co2 = round(sum([t.co2_kg() for t in transports]), 2)
        energy_co2 = round(sum([e.co2_kg() for e in energies]), 2)
        waste_co2 = round(sum([w.co2_kg() for w in wastes]), 2)
        water_co2 = round(sum([w.co2_kg() for w in waters]), 2)
        report_title = f"KCIC Carbon Footprint Report — {user.username}"
        report_name = user.username

    total_co2 = round(transport_co2 + energy_co2 + waste_co2 + water_co2, 2)

    if total_co2 == 0:
        carbon_score = 'N/A'
    elif total_co2 <= 5:
        carbon_score = 'A'
    elif total_co2 <= 15:
        carbon_score = 'B'
    elif total_co2 <= 30:
        carbon_score = 'C'
    else:
        carbon_score = 'D'

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="carbon_report_{report_name}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFillColorRGB(0.18, 0.49, 0.20)
    p.rect(0, height-80, width, 80, fill=True, stroke=False)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height-50, report_title)

    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 12)
    p.drawString(50, height-110, f"Month: {date(current_year, current_month, 1).strftime('%B %Y')}")
    p.drawString(50, height-130, f"Generated: {date.today()}")
    if department not in ['manager', 'kcic_admin']:
        p.drawString(50, height-150, f"User: {user.username}")
        p.drawString(50, height-170, f"Department: {department.replace('_', ' ').title()}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height-210, "Monthly Emissions Summary:")

    p.setFont("Helvetica", 12)
    p.drawString(70, height-240, f"Transport:  {transport_co2} kg CO2")
    p.drawString(70, height-260, f"Energy:     {energy_co2} kg CO2")
    p.drawString(70, height-280, f"Waste:      {waste_co2} kg CO2")
    p.drawString(70, height-300, f"Water:      {water_co2} kg CO2")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height-340, f"Total CO2 This Month: {total_co2} kg")
    p.drawString(50, height-365, f"Carbon Score: {carbon_score}")

    p.showPage()
    p.save()
    return response

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    current_month = timezone.now().month
    current_year = timezone.now().year

    from .models import UserProfile
    departments = {
        'field_operations': {'name': '🚛 Field Operations', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
        'processing_plant': {'name': '🏭 Processing Plant', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
        'water_sanitation': {'name': '💧 Water & Sanitation', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
        'waste_management': {'name': '♻️ Waste Management', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
    }

    profiles = UserProfile.objects.exclude(department='manager')
    for profile in profiles:
        u = profile.user
        dept = profile.department
        if dept in departments:
            t = sum([x.co2_kg() for x in Transportation.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            e = sum([x.co2_kg() for x in EnergyUsage.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            w = sum([x.co2_kg() for x in WasteData.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            wa = sum([x.co2_kg() for x in WaterUsage.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            departments[dept]['transport'] += t
            departments[dept]['energy'] += e
            departments[dept]['waste'] += w
            departments[dept]['water'] += wa
            departments[dept]['total'] += round(t + e + w + wa, 2)

    for dept in departments:
        total = departments[dept]['total']
        if total == 0:
            departments[dept]['score'] = 'N/A'
        elif total <= 5:
            departments[dept]['score'] = 'A'
        elif total <= 15:
            departments[dept]['score'] = 'B'
        elif total <= 30:
            departments[dept]['score'] = 'C'
        else:
            departments[dept]['score'] = 'D'
        departments[dept]['total'] = round(total, 2)

    dept_list = list(departments.values())
    total_company = round(sum([d['total'] for d in dept_list]), 2)

    context = {
        'dept_list': dept_list,
        'total_company': total_company,
        'current_month': date(current_year, current_month, 1).strftime('%B %Y'),
    }
    return render(request, 'footprint/admin_dashboard.html', context)


@login_required
def manager_dashboard(request):
    try:
        profile = request.user.userprofile
        if profile.department != 'manager':
            return redirect('dashboard')
    except:
        pass

    current_month = timezone.now().month
    current_year = timezone.now().year

    from .models import UserProfile
    departments = {
        'field_operations': {'name': '🚛 Field Operations', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
        'processing_plant': {'name': '🏭 Processing Plant', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
        'water_sanitation': {'name': '💧 Water & Sanitation', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
        'waste_management': {'name': '♻️ Waste Management', 'transport': 0, 'energy': 0, 'waste': 0, 'water': 0, 'total': 0},
    }

    profiles = UserProfile.objects.exclude(department='manager')
    for profile in profiles:
        u = profile.user
        dept = profile.department
        if dept in departments:
            t = sum([x.co2_kg() for x in Transportation.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            e = sum([x.co2_kg() for x in EnergyUsage.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            w = sum([x.co2_kg() for x in WasteData.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            wa = sum([x.co2_kg() for x in WaterUsage.objects.filter(user=u, date__month=current_month, date__year=current_year)])
            departments[dept]['transport'] += t
            departments[dept]['energy'] += e
            departments[dept]['waste'] += w
            departments[dept]['water'] += wa
            departments[dept]['total'] += round(t + e + w + wa, 2)

    for dept in departments:
        total = departments[dept]['total']
        if total == 0:
            departments[dept]['score'] = 'N/A'
        elif total <= 5:
            departments[dept]['score'] = 'A'
        elif total <= 15:
            departments[dept]['score'] = 'B'
        elif total <= 30:
            departments[dept]['score'] = 'C'
        else:
            departments[dept]['score'] = 'D'
        departments[dept]['total'] = round(total, 2)

    dept_list = list(departments.values())
    total_company = round(sum([d['total'] for d in dept_list]), 2)

    context = {
        'dept_list': dept_list,
        'total_company': total_company,
        'current_month': date(current_year, current_month, 1).strftime('%B %Y'),
    }
    return render(request, 'footprint/manager_dashboard.html', context)


@login_required
def data_history(request):
    user = request.user
    try:
        profile = user.userprofile
        department = profile.department
    except:
        if user.is_staff:
            department = 'kcic_admin'
        else:
            department = 'manager'

    transports = Transportation.objects.filter(user=user).order_by('-date')
    energies = EnergyUsage.objects.filter(user=user).order_by('-date')
    wastes = WasteData.objects.filter(user=user).order_by('-date')
    waters = WaterUsage.objects.filter(user=user).order_by('-date')

    context = {
        'transports': transports,
        'energies': energies,
        'wastes': wastes,
        'waters': waters,
        'department': department,
    }
    return render(request, 'footprint/data_history.html', context)