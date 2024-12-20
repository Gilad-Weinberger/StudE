from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, datetime
from .models import *
from django.db.models import Avg, F

@login_required
def Dashboard(request):
    user = request.user
    current_date = date.today()

    classes = Class.objects.filter(user=user)[:3]

    context = {
        "user": user,
        "classes": classes,
        "current_date": current_date
    }
    
    return render(request, 'base/dashboard.html', context)

@login_required
def Classes(request):
    user = request.user
    classes = Class.objects.filter(user=user)
    current_date = date.today()

    context = {
        "user": user,
        "classes": classes,
        "current_date": current_date
    }

    return render(request, 'base/classes.html', context)

@login_required
def create_class(request):
    user = request.user
    
    class_obj = Class.objects.create(
        user=user,
        name="New Class",
    )
    return redirect('base:classes')

@login_required
def Class_Page(request, class_id):
    user = request.user
    class_obj = Class.objects.prefetch_related('exam_set', 'assignment_set').get(id=class_id)

    exams = class_obj.exam_set.all()
    assignments = class_obj.assignment_set.all()

    current_date = date.today() 

    context = {
        "user": user,
        "class": class_obj,
        "exams": exams,
        "assignments": assignments,
        "current_date": current_date
    }

    return render(request, 'base/class.html', context)

@login_required
def Assignments(request):
    user = request.user
    assignments = Assignment.objects.filter(user=user)
    classes = Class.objects.prefetch_related('assignment_set').filter(user=user)
    current_date = date.today()

    context = {
        "user": user,
        "assignments": assignments,
        "classes": classes,
        "status_choices": Assignment.STATUS_CHOICES,
        "current_date": current_date
    }

    return render(request, 'base/assignments.html', context)

@login_required
def create_assignment(request):
    user = request.user
    
    assignment = Assignment.objects.create(
        user=user,
        due_date=datetime.now(),
    )
    return redirect('base:assignments')

@login_required
def update_assignment(request, assignment_id):
    if request.method == 'POST':
        try:
            assignment = Assignment.objects.get(id=assignment_id, user=request.user)
            field = request.POST.get('field')
            value = request.POST.get('value')
            
            if field == 'name':
                assignment.name = value
            elif field == 'class_obj':
                class_obj = Class.objects.get(id=value, user=request.user)
                assignment.class_obj = class_obj
            elif field == 'description':
                assignment.description = value
            elif field == 'due_date':
                assignment.due_date = value
            elif field == 'status':
                assignment.status = value
            elif field == 'grade':
                assignment.grade = value if value else None
                
            assignment.save()
            
            # Return formatted values in response
            response_data = {
                'status': 'success',
                'value': value,
            }
            
            # Add specific formatting for different field types
            if field == 'due_date':
                response_data['formatted_date'] = assignment.due_date.strftime('%d/%m/%Y %H:%M')
            elif field == 'class_obj':
                response_data['value'] = assignment.class_obj.name
            elif field == 'grade':
                response_data['value'] = str(assignment.grade) if assignment.grade is not None else '-'
            elif field == 'status':
                response_data['value'] = dict(Assignment.STATUS_CHOICES)[value]
                
            return JsonResponse(response_data)
            
        except (Assignment.DoesNotExist, Class.DoesNotExist) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': 'Invalid value provided'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def Exams(request):
    user = request.user
    exams = Exam.objects.filter(user=user)
    classes = Class.objects.filter(user=user)
    current_date = date.today()

    context = {
        "user": user,
        "exams": exams,
        "classes": classes,
        "current_date": current_date
    }

    return render(request, 'base/exams.html', context)

@login_required
def create_exam(request):
    user = request.user
    
    exam = Exam.objects.create(
        user=user,
        date=date.today(),
    )
    return redirect('base:exams')

@login_required
def update_exam(request, exam_id):
    if request.method == 'POST':
        try:
            exam = Exam.objects.get(id=exam_id, user=request.user)
            field = request.POST.get('field')
            value = request.POST.get('value')
            
            if field == 'name':
                exam.name = value
            elif field == 'class_obj':
                class_obj = Class.objects.get(id=value, user=request.user)
                exam.class_obj = class_obj
            elif field == 'date':
                exam.date = value
            elif field == 'grade':
                exam.grade = value if value else None
                
            exam.save()
            
            # Return updated values in response
            response_data = {
                'status': 'success',
                'value': str(getattr(exam, field)) if field != 'class_obj' else exam.class_obj.name,
                'formatted_date': exam.date.strftime('%d/%m/%Y') if field == 'date' else None
            }
            return JsonResponse(response_data)
            
        except (Exam.DoesNotExist, Class.DoesNotExist, ValueError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def Grades(request):
    user = request.user
    assignments = Assignment.objects.filter(user=user, grade__isnull=False).values('class_obj', 'grade')
    exams = Exam.objects.filter(user=user, grade__isnull=False).values('class_obj', 'grade')
    current_date = date.today()

    if assignments:
        assignments_avg = sum(assignment['grade'] for assignment in assignments) / len(assignments)
    else:
        assignments_avg = "None"

    if exams:
        exams_avg = sum(exam['grade'] for exam in exams) / len(exams)
    else:
        exams_avg = "None"

    # Calculate best class using separate averages for assignments and exams
    best_class = Class.objects.filter(user=user).annotate(
        assignment_avg=Avg('assignment__grade'),
        exam_avg=Avg('exam__grade')
    ).order_by(
        (F('assignment_avg') + F('exam_avg')) / 2
    ).first()

    # Calculate best class average
    if best_class and (best_class.assignment_avg is not None or best_class.exam_avg is not None):
        assignment_avg = best_class.assignment_avg or 0
        exam_avg = best_class.exam_avg or 0
        best_class.avg = (assignment_avg + exam_avg) / 2
    else:
        best_class.avg = "None"

    context = {
        "user": user,
        "current_date": current_date,
        "assignments_avg": assignments_avg,
        "exams_avg": exams_avg,
        "best_class": best_class
    }
    return render(request, 'base/grades.html', context)
