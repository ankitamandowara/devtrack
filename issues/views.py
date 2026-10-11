import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Reporter, Issue, CriticalIssue, LowPriorityIssue

REPORTERS_FILE = settings.BASE_DIR / 'reporters.json'
ISSUES_FILE = settings.BASE_DIR / 'issues.json'


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

@csrf_exempt
def issues(request):
    if request.method == 'POST':
        return create_issue(request)
    if request.method == 'GET':
        return get_issues(request)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def create_issue(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    for field in ['id', 'title', 'description', 'status', 'priority', 'reporter_id']:
        if field not in data:
            return JsonResponse({'error': f'{field} is required'}, status=400)

    if data['priority'] == 'critical':
        issue = CriticalIssue(data['id'], data['title'], data['description'],
                              data['status'], data['priority'], data['reporter_id'])
    elif data['priority'] == 'low':
        issue = LowPriorityIssue(data['id'], data['title'], data['description'],
                                 data['status'], data['priority'], data['reporter_id'])
    else:
        issue = Issue(data['id'], data['title'], data['description'],
                      data['status'], data['priority'], data['reporter_id'])

    try:
        issue.validate()
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    all_reporters = read_json(REPORTERS_FILE)
    if not any(r['id'] == issue.reporter_id for r in all_reporters):
        return JsonResponse({'error': 'Reporter not found'}, status=400)

    all_issues = read_json(ISSUES_FILE)
    for i in all_issues:
        if i['id'] == issue.id:
            return JsonResponse({'error': 'Issue ID already exists'}, status=400)

    all_issues.append(issue.to_dict())
    write_json(ISSUES_FILE, all_issues)

    response_data = issue.to_dict()
    response_data['message'] = issue.describe()
    return JsonResponse(response_data, status=201)


def get_issues(request):
    all_issues = read_json(ISSUES_FILE)
    issue_id = request.GET.get('id')
    status = request.GET.get('status')

    if issue_id is not None:
        try:
            issue_id = int(issue_id)
        except ValueError:
            return JsonResponse({'error': 'id must be a number'}, status=400)
        for i in all_issues:
            if i['id'] == issue_id:
                return JsonResponse(i, status=200)
        return JsonResponse({'error': 'Issue not found'}, status=404)

    if status is not None:
        filtered = [i for i in all_issues if i['status'] == status]
        return JsonResponse(filtered, safe=False, status=200)

    return JsonResponse(all_issues, safe=False, status=200)