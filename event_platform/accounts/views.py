from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .crud.create import (
    create_participant,
    create_organizer,
    create_user
)
from .crud.read import (
    get_user_by_email,
    get_participant_by_id,
    get_participant_by_student_id,
    get_organizer_by_id,
    get_organizer_by_name,
)
from .crud.update import (
    update_participant,
    update_organizer,
    update_user
)
from .form_choices import COURSES, ORGANIZATIONS

def home(request):
    if not request.session.get('user_id'):
        return redirect('login')

    return redirect('event_list')

def _render_register(request, role, error=None):
    is_post = request.method == 'POST'

    return render(request, 'register.html', {
        'error': error,
        'role': role,
        'courses': COURSES,
        'all_organizations': ORGANIZATIONS,
        'form': request.POST if is_post else {},
        'selected_orgs': request.POST.getlist('organizations') if is_post else [],
    })

def register(request):
    return redirect('participant_register')

def participant_register(request):
    if request.method != 'POST':
        return _render_register(request, 'student')

    email = request.POST.get('email', '').strip().lower()
    id_number = request.POST.get('idNumber', '').strip()
    password = request.POST.get('password', '')
    first_name = request.POST.get('firstName', '').strip()
    last_name = request.POST.get('lastName', '').strip()
    course = request.POST.get('course', '').strip()

    if not all([email, id_number, password, first_name, last_name, course]):
        return _render_register(request, 'student', 'Please fill in all required fields.')

    if get_user_by_email(email):
        return _render_register(request, 'student', 'Email is already registered.')

    if get_participant_by_student_id(id_number):
        return _render_register(request, 'student', 'Student ID is already registered.')

    try:
        year = int(request.POST.get('year'))
    except (ValueError, TypeError):
        return _render_register(request, 'student', 'Please enter a valid year level.')

    participant = {
        'idNumber': id_number,
        'firstName': first_name,
        'lastName': last_name,
        'year': year,
        'course': course,
        'email': email,
        'organizations': request.POST.getlist('organizations')
    }
    result = create_participant(participant)

    create_user({
        'email': email,
        'password': make_password(password),
        'role': 'participant',
        'profileId': result.inserted_id
    })

    return redirect('login')

def organizer_register(request):
    if request.method != 'POST':
        return _render_register(request, 'organization')

    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    organization_name = request.POST.get('organizationName', '').strip()

    if not all([email, password, organization_name]):
        return _render_register(request, 'organization', 'Please fill in all required fields.')

    if get_user_by_email(email):
        return _render_register(request, 'organization', 'Email is already registered.')

    if get_organizer_by_name(organization_name):
        return _render_register(request, 'organization', 'Organization is already registered.')

    result = create_organizer({
        'organizationName': organization_name,
        'email': email
    })

    create_user({
        'email': email,
        'password': make_password(password),
        'role': 'organizer',
        'profileId': result.inserted_id
    })

    return redirect('login')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = get_user_by_email(email)

        if user and check_password(password, user['password']):
            request.session['user_id'] = str(user['_id'])
            request.session['role'] = user['role']
            request.session['profile_id'] = str(user['profileId'])

            if user['role'] == 'organizer':
                organizer = get_organizer_by_id(user['profileId'])
                if organizer:
                    request.session['name'] = organizer['organizationName']

            elif user['role'] == 'participant':
                participant = get_participant_by_id(user['profileId'])
                if participant:
                    request.session['name'] = participant['firstName'] + " " + participant['lastName']

            return redirect('event_list')

        return render(request, 'login.html', {
            'error': 'Invalid email or password.',
            'form': request.POST,
        })

    return render(request, 'login.html')

def logout(request):
    request.session.flush()
    return redirect('login')

def edit_profile(request):
    if not request.session.get('user_id'):
        return redirect('event_list')

    role = request.session.get('role')
    profile_id = request.session.get('profile_id')
    user_id = request.session.get('user_id')

    if role == 'participant':
        profile = get_participant_by_id(profile_id)
    elif role == 'organizer':
        profile = get_organizer_by_id(profile_id)
    else:
        return redirect('event_list')

    if not profile:
        messages.error(request, 'Profile not found.')
        return redirect('event_list')

    context = {
        'profile': profile,
        'role': role,
        'courses': COURSES,
        'all_organizations': ORGANIZATIONS,
        'selected_orgs': (request.POST.getlist('organizations')
                        if request.method == 'POST' else profile.get('organizations', [])),
    }

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        existing_user = get_user_by_email(email)

        if existing_user and str(existing_user['_id']) != user_id:
            messages.error(request, 'Email is already registered.')
            return render(request, 'edit_profile.html', context)

        if role == 'participant':
            try:
                updated_data = {
                    'idNumber': request.POST.get('idNumber', '').strip(),
                    'firstName': request.POST.get('firstName', '').strip(),
                    'lastName': request.POST.get('lastName', '').strip(),
                    'year': int(request.POST.get('year')),
                    'course': request.POST.get('course', '').strip(),
                    'email': email,
                    'organizations': request.POST.getlist('organizations')
                }
            except (ValueError, TypeError):
                messages.error(request, 'Please enter a valid year level.')
                return render(request, 'edit_profile.html', context)

            update_participant(profile_id, updated_data)
            request.session['name'] = f"{updated_data['firstName']} {updated_data['lastName']}"

        elif role == 'organizer':
            organization_name = request.POST.get('organizationName', '').strip()
            existing_org = get_organizer_by_name(organization_name)

            if existing_org and str(existing_org['_id']) != profile_id:
                messages.error(request, 'Organization is already registered.')
                return render(request, 'edit_profile.html', context)

            update_organizer(profile_id, {
                'organizationName': organization_name,
                'email': email,
            })
            request.session['name'] = organization_name

        update_user(user_id, {'email': email})

        messages.success(request, 'Profile updated successfully!')
        return redirect('event_list')

    return render(request, 'edit_profile.html', context)