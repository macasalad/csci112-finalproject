from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .crud.create import create_participant, create_organizer, create_user
from .crud.read import (
    get_user_by_email,
    get_participant_by_id,
    get_participant_by_student_id,
    get_organizer_by_id,
    get_organizer_by_name
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

    return render(request, 'home.html')


# ---------- Registration ----------

def _render_register(request, role):
    """
    Both /register/participant/ and /register/organizer/ use register.html.
    `role` ('student' or 'organization') picks the active tab, the visible
    fields and the URL the form posts to. On a failed POST the typed values
    are sent back so the user doesn't have to retype everything.
    """
    is_post = request.method == 'POST'
    return render(request, 'register.html', {
        'role': role,
        'courses': COURSES,
        'all_organizations': ORGANIZATIONS,
        'form': request.POST if is_post else {},
        'selected_orgs': request.POST.getlist('organizations') if is_post else [],
    })


def register(request):
    # /register/ on its own just opens the student tab.
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

    # The form uses `novalidate`, so the browser won't block empty fields.
    if not all([email, id_number, password, first_name, last_name, course]):
        messages.error(request, 'Please fill in all required fields.')
        return _render_register(request, 'student')

    if get_user_by_email(email):
        messages.error(request, 'Email is already registered.')
        return _render_register(request, 'student')

    if get_participant_by_student_id(id_number):
        messages.error(request, 'Student ID is already registered.')
        return _render_register(request, 'student')

    try:
        year = int(request.POST.get('year'))
    except (ValueError, TypeError):
        messages.error(request, 'Please enter a valid year level.')
        return _render_register(request, 'student')

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

    messages.success(request, 'Account created. You can now sign in.')
    return redirect('login')


def organizer_register(request):
    if request.method != 'POST':
        return _render_register(request, 'organization')

    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    organization_name = request.POST.get('organizationName', '').strip()

    if not all([email, password, organization_name]):
        messages.error(request, 'Please fill in all required fields.')
        return _render_register(request, 'organization')

    if get_user_by_email(email):
        messages.error(request, 'Email is already registered.')
        return _render_register(request, 'organization')

    if get_organizer_by_name(organization_name):
        messages.error(request, 'Organization is already registered.')
        return _render_register(request, 'organization')

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

    messages.success(request, 'Account created. You can now sign in.')
    return redirect('login')


# ---------- Auth ----------

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

            messages.success(request, 'Login successful!')
            return redirect('home')

        messages.error(request, 'Invalid email or password.')
        return render(request, 'login.html', {'form': request.POST})

    return render(request, 'login.html')


def logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# ---------- Profile ----------

def edit_profile(request):
    if not request.session.get('user_id'):
        return redirect('home')

    role = request.session.get('role')
    profile_id = request.session.get('profile_id')
    user_id = request.session.get('user_id')

    if role == 'participant':
        profile = get_participant_by_id(profile_id)
    elif role == 'organizer':
        profile = get_organizer_by_id(profile_id)
    else:
        return redirect('home')

    if not profile:
        messages.error(request, 'Profile not found.')
        return redirect('home')

    context = {
        'profile': profile,
        'role': role,
        'courses': COURSES,
        'all_organizations': ORGANIZATIONS
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
        return redirect('home')

    return render(request, 'edit_profile.html', context)