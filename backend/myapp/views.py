from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ObjetDefectueux, ActivityLog, ImageAnalysis
from .forms import ObjetDefectueuxForm, SignUpForm
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.contrib.auth.models import User
from .utils import log_activity
from django.contrib.auth.forms import UserCreationForm
from .services.ai_service import DefectDetectionService
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .services.yolo_service import DefectDetectionYOLO
from django.core.files.base import File

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            log_activity(
                request,
                'LOGIN',
                object_name=user.username,
                details=f"User logged in: {user.username}"
            )
            messages.success(request, 'Login successful.')
            # Get the next parameter or default to objetdefectueux_list
            next_url = request.GET.get('next', 'objetdefectueux_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'myapp/login.html')

@login_required
def logout_view(request):
    if request.user.is_authenticated:
        log_activity(
            request,
            'LOGOUT',
            object_name=request.user.username,
            details=f"User logged out: {request.user.username}"
        )
        messages.success(request, 'You have been logged out successfully.')
    logout(request)
    return redirect('login')

# Helper function to check if user is admin
def is_admin(user):
    return user.is_staff

@login_required(login_url='login')
def objetdefectueux_list(request):
    try:
        # Get all non-deleted objects
        objets = ObjetDefectueux.objects.filter(deleted_at__isnull=True)
        
        # Handle search and filtering
        query = request.GET.get('q')
        status = request.GET.get('status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if query:
            objets = objets.filter(name__icontains=query)
        if status:
            objets = objets.filter(status=status)
        if date_from:
            objets = objets.filter(inspection_date__gte=date_from)
        if date_to:
            objets = objets.filter(inspection_date__lte=date_to)
            
        # Sorting
        sort_by = request.GET.get('sort', '-inspection_date')
        objets = objets.order_by(sort_by)
        
        # Pagination
        paginator = Paginator(objets, 10)
        page = request.GET.get('page')
        objets = paginator.get_page(page)
        
        return render(request, 'myapp/objetdefectueux_list.html', {
            'objets': objets,
            'status_choices': ObjetDefectueux.STATUS_CHOICES,
            'is_admin': request.user.is_staff
        })
    except Exception as e:
        messages.error(request, f"An error occurred while loading the list: {str(e)}")
        return render(request, 'myapp/objetdefectueux_list.html', {
            'objets': [],
            'status_choices': ObjetDefectueux.STATUS_CHOICES,
            'is_admin': request.user.is_staff
        })

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='objetdefectueux_list')
def objetdefectueux_create(request):
    if not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        form = ObjetDefectueuxForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                log_activity(
                    request,
                    'CREATE',
                    object_id=obj.id,
                    object_name=str(obj),
                    details=f"Created new defective object: {obj}"
                )
                messages.success(request, f"Object '{obj.name}' successfully created.")
                return redirect('objetdefectueux_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création: {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ObjetDefectueuxForm()
    
    return render(request, 'myapp/objetdefectueux_form.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='objetdefectueux_list')
def objetdefectueux_edit(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    try:
        objet = get_object_or_404(ObjetDefectueux, pk=pk)
        if request.method == 'POST':
            form = ObjetDefectueuxForm(request.POST, instance=objet)
            if form.is_valid():
                form.save()
                messages.success(request, "Object successfully updated.")
                return redirect('objetdefectueux_list')
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        else:
            form = ObjetDefectueuxForm(instance=objet)
    except ObjetDefectueux.DoesNotExist:
        messages.error(request, "L'objet demandé n'existe pas.")
        return redirect('objetdefectueux_list')
    except Exception as e:
        messages.error(request, f"Une erreur s'est produite: {str(e)}")
        return redirect('objetdefectueux_list')
    
    return render(request, 'myapp/objetdefectueux_form.html', {'form': form, 'objet': objet})

@login_required(login_url='login')
@user_passes_test(is_admin)
def objetdefectueux_delete(request, pk):
    try:
        objet = get_object_or_404(ObjetDefectueux, pk=pk)
        if request.method == 'POST':
            name = objet.name
            objet.deleted_at = timezone.now()
            objet.save()
            log_activity(
                request,
                'DELETE',
                object_id=pk,
                object_name=name,
                details=f"Deleted defective object: {name}"
            )
            messages.warning(
                request, 
                f'Object "{name}" has been deleted. <a href="{reverse("objetdefectueux_restore", args=[pk])}" class="alert-link undo-delete">Undo</a>',
                extra_tags='safe'
            )
            return redirect('objetdefectueux_list')
    except ObjetDefectueux.DoesNotExist:
        messages.error(request, "L'objet à supprimer n'existe pas.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression: {str(e)}")
    
    return render(request, 'myapp/objetdefectueux_confirm_delete.html', {'objet': objet})

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='objetdefectueux_list')
def objetdefectueux_restore(request, pk):
    if not request.user.is_staff:
        raise PermissionDenied
    try:
        objet = get_object_or_404(ObjetDefectueux, pk=pk)
        objet.deleted_at = None
        objet.save()
        messages.success(request, "Object successfully restored.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la restauration: {str(e)}")
    
    return redirect('objetdefectueux_list')

@login_required(login_url='login')
def objetdefectueux_detail(request, pk):
    try:
        object = get_object_or_404(ObjetDefectueux, pk=pk)
        log_activity(
            request,
            'VIEW',
            object_id=object.id,
            object_name=str(object),
            details=f"Viewed defective object: {object}"
        )
        return render(request, 'myapp/objetdefectueux_detail.html', {
            'object': object,
            'is_admin': request.user.is_staff
        })
    except Exception as e:
        messages.error(request, f"Error loading object details: {str(e)}")
        return redirect('objetdefectueux_list')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(
                request,
                'CREATE',
                object_name=f"User: {user.username}",
                details="New user registration"
            )
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'myapp/signup.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(lambda u: u.is_staff)
def activity_log(request):
    logs = ActivityLog.objects.all()
    
    # Filter by user
    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user__username=user_filter)
    
    # Filter by action
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Search by object name
    search = request.GET.get('search')
    if search:
        logs = logs.filter(object_name__icontains=search)
    
    # Pagination
    paginator = Paginator(logs, 20)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'users': User.objects.all(),
        'action_types': ActivityLog.ACTION_TYPES,
        'current_filters': {
            'user': user_filter,
            'action': action_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    }
    
    return render(request, 'myapp/activity_log.html', context)

@login_required(login_url='login')
def analyze_image(request, pk):
    objet = get_object_or_404(ObjetDefectueux, pk=pk)
    
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Save the image analysis record
            analysis = ImageAnalysis.objects.create(
                objet_defectueux=objet,
                image=request.FILES['image']
            )
            
            # Get the file path
            image_path = analysis.image.path
            
            # Initialize AI service and analyze image
            ai_service = DefectDetectionService()
            result = ai_service.analyze_image(image_path)
            
            if 'error' not in result:
                # Update analysis with results
                analysis.prediction = result['prediction']
                analysis.is_defective = result['is_defective']
                analysis.confidence_score = result['confidence']
                analysis.recommendations = result['recommendations']
                analysis.save()
                
                # Log the activity
                log_activity(
                    request,
                    'AI_ANALYSIS',
                    object_id=objet.id,
                    object_name=str(objet),
                    details=f"AI Analysis completed: {'Defective' if result['is_defective'] else 'Non-defective'}"
                )
                
                messages.success(request, 'Image analysis completed successfully.')
            else:
                messages.error(request, f"Analysis failed: {result['error']}")
                analysis.delete()  # Clean up failed analysis
                
        except Exception as e:
            messages.error(request, f"Error during analysis: {str(e)}")
            
    return redirect('objetdefectueux_detail', pk=pk)

@login_required(login_url='login')
def ai_analysis_view(request, pk):
    objet = get_object_or_404(ObjetDefectueux, pk=pk)
    analyses = ImageAnalysis.objects.filter(objet_defectueux=objet).order_by('-analysis_date')
    
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Sauvegarder l'analyse d'image
            analysis = ImageAnalysis.objects.create(
                objet_defectueux=objet,
                image=request.FILES['image']
            )
            
            # Initialiser le service YOLO et analyser l'image
            yolo_service = DefectDetectionYOLO()
            result = yolo_service.analyze_image(analysis.image.path)
            
            if 'error' not in result:
                # Mettre à jour l'analyse avec les résultats
                analysis.is_defective = result['is_defective']
                analysis.confidence_score = result['confidence']
                analysis.detections = result['detections']
                analysis.recommendations = result['recommendations']
                
                # Sauvegarder l'image annotée
                if 'annotated_image' in result and os.path.exists(result['annotated_image']):
                    with open(result['annotated_image'], 'rb') as f:
                        analysis.annotated_image.save(
                            os.path.basename(result['annotated_image']),
                            File(f),
                            save=True
                        )
                
                analysis.save()
                
                messages.success(request, "L'analyse d'image a été complétée avec succès.")
            else:
                messages.error(request, f"Échec de l'analyse: {result['error']}")
                analysis.delete()
                
        except Exception as e:
            messages.error(request, f"Erreur pendant l'analyse: {str(e)}")
    
    context = {
        'object': objet,
        'analyses': analyses
    }
    return render(request, 'myapp/ai_analysis.html', context)

@login_required(login_url='login')
@require_POST
def clear_analysis_history(request, pk):
    try:
        objet = get_object_or_404(ObjetDefectueux, pk=pk)
        analyses = ImageAnalysis.objects.filter(objet_defectueux=objet)
        count = analyses.count()
        analyses.delete()
        
        log_activity(
            request,
            'DELETE',
            object_id=objet.id,
            object_name=str(objet),
            details=f"Cleared {count} analysis records"
        )
        
        messages.success(request, f'Successfully cleared {count} analysis records.')
        return redirect('ai_analysis', pk=pk)
    except Exception as e:
        messages.error(request, f"Error clearing history: {str(e)}")
        return redirect('ai_analysis', pk=pk)

@login_required(login_url='login')
def yolo_analysis_view(request, pk):
    objet = get_object_or_404(ObjetDefectueux, pk=pk)
    analyses = ImageAnalysis.objects.filter(objet_defectueux=objet, analysis_type='YOLO').order_by('-analysis_date')
    
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            analysis = ImageAnalysis.objects.create(
                objet_defectueux=objet,
                image=request.FILES['image'],
                analysis_type='YOLO'  # Marquer comme analyse YOLO
            )
            
            yolo_service = DefectDetectionYOLO()
            result = yolo_service.analyze_image(analysis.image.path)
            
            if 'error' not in result:
                analysis.is_defective = result['is_defective']
                analysis.confidence_score = result['confidence']
                analysis.detections = result['detections']
                analysis.recommendations = result['recommendations']
                
                if 'annotated_image' in result and os.path.exists(result['annotated_image']):
                    with open(result['annotated_image'], 'rb') as f:
                        analysis.annotated_image.save(
                            os.path.basename(result['annotated_image']),
                            File(f),
                            save=True
                        )
                
                analysis.save()
                messages.success(request, 'Analyse YOLO complétée avec succès.')
            else:
                messages.error(request, f"Erreur d'analyse: {result['error']}")
                analysis.delete()
                
        except Exception as e:
            messages.error(request, f"Erreur pendant l'analyse: {str(e)}")
    
    context = {
        'object': objet,
        'analyses': analyses,
        'analysis_type': 'YOLO'
    }
    return render(request, 'myapp/yolo_analysis.html', context)

@login_required(login_url='login')
def basic_analysis_view(request, pk):
    objet = get_object_or_404(ObjetDefectueux, pk=pk)
    analyses = ImageAnalysis.objects.filter(objet_defectueux=objet, analysis_type='BASIC').order_by('-analysis_date')
    
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            analysis = ImageAnalysis.objects.create(
                objet_defectueux=objet,
                image=request.FILES['image'],
                analysis_type='BASIC'  # Marquer comme analyse basique
            )
            
            basic_service = DefectDetectionService()
            result = basic_service.analyze_image(analysis.image.path)
            
            if 'error' not in result:
                analysis.is_defective = result['is_defective']
                analysis.confidence_score = result['confidence']
                analysis.recommendations = result['recommendations']
                analysis.save()
                
                messages.success(request, 'Analyse basique complétée avec succès.')
            else:
                messages.error(request, f"Erreur d'analyse: {result['error']}")
                analysis.delete()
                
        except Exception as e:
            messages.error(request, f"Erreur pendant l'analyse: {str(e)}")
    
    context = {
        'object': objet,
        'analyses': analyses,
        'analysis_type': 'BASIC'
    }
    return render(request, 'myapp/basic_analysis.html', context)

