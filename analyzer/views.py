import json
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage
from .services import analyze_transactions, generate_ai_advice


def index(request):
    """Landing page with file upload."""
    return render(request, 'analyzer/index.html')


def upload_and_analyze(request):
    """Handle CSV upload and run analysis."""
    if request.method != 'POST':
        return redirect('index')

    if 'csv_file' not in request.FILES:
        return render(request, 'analyzer/index.html', {'error': 'Please select a CSV file to upload.'})

    csv_file = request.FILES['csv_file']

    if not csv_file.name.endswith('.csv'):
        return render(request, 'analyzer/index.html', {'error': 'Only CSV files are supported.'})

    # Save temporarily
    upload_path = os.path.join(settings.MEDIA_ROOT, 'uploads', csv_file.name)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    with open(upload_path, 'wb+') as dest:
        for chunk in csv_file.chunks():
            dest.write(chunk)

    # Analyze
    result = analyze_transactions(upload_path)

    if 'error' in result:
        return render(request, 'analyzer/index.html', {
            'error': result['error'],
            'columns': result.get('columns', [])
        })

    # Generate AI advice
    advice = generate_ai_advice(result)
    result['ai_advice'] = advice

    # Store in session (convert to JSON-safe)
    request.session['analysis'] = json.dumps(result, default=str)
    request.session['filename'] = csv_file.name

    # Clean up file
    try:
        os.remove(upload_path)
    except Exception:
        pass

    return redirect('dashboard')


def dashboard(request):
    """Show the analysis dashboard."""
    analysis_json = request.session.get('analysis')
    if not analysis_json:
        return redirect('index')

    analysis = json.loads(analysis_json)
    filename = request.session.get('filename', 'transactions.csv')

    return render(request, 'analyzer/dashboard.html', {
        'analysis': analysis,
        'analysis_json': analysis_json,
        'filename': filename,
    })


def clear_session(request):
    """Clear session and go back to upload."""
    request.session.flush()
    return redirect('index')
