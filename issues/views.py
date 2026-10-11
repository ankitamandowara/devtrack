import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Reporter

REPORTERS_FILE = settings.BASE_DIR / 'reporters.json'


def read_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


@csrf_exempt
def reporters(request):
    if request.method == 'POST':
        return create_reporter(request)
    if request.method == 'GET':
        return get_reporters(request)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def create_reporter(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    for field in ['id', 'name', 'email', 'team']:
        if field not in data:
            return JsonResponse({'error': f'{field} is required'}, status=400)

    reporter = Reporter(data['id'], data['name'], data['email'], data['team'])

    try:
        reporter.validate()
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    all_reporters = read_json(REPORTERS_FILE)
    for r in all_reporters:
        if r['id'] == reporter.id:
            return JsonResponse({'error': 'Reporter ID already exists'}, status=400)

    all_reporters.append(reporter.to_dict())
    write_json(REPORTERS_FILE, all_reporters)
    return JsonResponse(reporter.to_dict(), status=201)


def get_reporters(request):
    all_reporters = read_json(REPORTERS_FILE)
    reporter_id = request.GET.get('id')

    if reporter_id is None:
        return JsonResponse(all_reporters, safe=False, status=200)

    try:
        reporter_id = int(reporter_id)
    except ValueError:
        return JsonResponse({'error': 'id must be a number'}, status=400)

    for r in all_reporters:
        if r['id'] == reporter_id:
            return JsonResponse(r, status=200)
    return JsonResponse({'error': 'Reporter not found'}, status=404)