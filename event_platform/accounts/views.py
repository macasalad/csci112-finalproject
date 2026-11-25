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

# Just to view
"""
def login_view(request):
    return render(request, "events/login.html")

def register_view(request): 
    return render(request, "events/register.html")
    """
##

def home(request):
    if not request.session.get('user_id'):
        return redirect('login')

    return render(request, 'home.html')

def register(request):
    return render(request, 'register.html')

def participant_register(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        id_number = request.POST.get('idNumber', '').strip()
        password = request.POST.get('password', '')

        # Check if email already exists
        if get_user_by_email(email):
            messages.error(request, 'Email is already registered.')
            return render(request, 'participant_register.html')

        # Check if student ID already exists
        if get_participant_by_student_id(id_number):
            messages.error(request, 'Student ID is already registered.')
            return render(request, 'participant_register.html')

        try:
            participant = {
                'idNumber': id_number,
                'firstName': request.POST.get('firstName', '').strip(),
                'lastName': request.POST.get('lastName', '').strip(),
                'year': int(request.POST.get('year')),
                'course': request.POST.get('course', '').strip(),
                'email': email,
                'organizations': request.POST.getlist('organizations')
            }

        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid year level.')
            return render(request, 'participant_register.html')

        result = create_participant(participant)

        user = {
            'email': email,
            'password': make_password(password),
            'role': 'participant',
            'profileId': result.inserted_id
        }

        create_user(user)

        messages.success(request, 'Participant registration successful!')
        return redirect('register')

    return render(request, 'participant_register.html', {
        'courses': COURSES,
        'all_organizations': ORGANIZATIONS
    })

def organizer_register(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Check if email already exists
        if get_user_by_email(email):
            messages.error(request, 'Email is already registered.')
            return render(request, 'organizer_register.html')

        organization_name = request.POST.get('organizationName', '').strip()

        if get_organizer_by_name(organization_name):
            messages.error(request, 'Organization is already registered.')
            return render(request, 'organizer_register.html')

        organizer = {
            'organizationName': organization_name,
            'email': email
        }

        result = create_organizer(organizer)

        user = {
            'email': email,
            'password': make_password(password),
            'role': 'organizer',
            'profileId': result.inserted_id
        }

        create_user(user)

        messages.success(request, 'Organizer registration successful!')
        return redirect('register')

    return render(request, 'organizer_register.html', {
        'all_organizations': ORGANIZATIONS
    })

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Find user by email
        user = get_user_by_email(email)

        if user and check_password(password, user['password']):
            # Store user information in session
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
        return render(request, 'login.html')

    return render(request, 'login.html')

def logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('login')

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

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        existing_user = get_user_by_email(email)

        if existing_user and str(existing_user['_id']) != user_id:
            messages.error(request, 'Email is already registered.')
            return render(request, 'edit_profile.html', {
                'profile': profile,
                'role': role,
                'courses': COURSES,
                'all_organizations': ORGANIZATIONS
            })

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
                return render(request, 'edit_profile.html', {
                    'profile': profile,
                    'role': role,
                    'courses': COURSES,
                    'all_organizations': ORGANIZATIONS
                })

            update_participant(profile_id, updated_data)
            request.session['name'] = f"{updated_data['firstName']} {updated_data['lastName']}"
        
        elif role == 'organizer':
            organization_name = request.POST.get('organizationName', '').strip()
            existing_org = get_organizer_by_name(organization_name)

            if existing_org and str(existing_org['_id']) != profile_id:
                messages.error(request, 'Organization is already registered.')
                return render(request, 'edit_profile.html', {
                    'profile': profile,
                    'role': role,
                    'courses': COURSES,
                    'all_organizations': ORGANIZATIONS
                })

            updated_data = {
                'organizationName': organization_name,
                'email': email,
            }

            update_organizer(profile_id, updated_data)
            request.session['name'] = organization_name

        update_user(user_id, {'email': email})

        messages.success(request, 'Profile updated successfully!')
        return redirect('home')

    return render(request, 'edit_profile.html', {
        'profile': profile,
        'role': role,
        'courses': COURSES,
        'all_organizations': ORGANIZATIONS
    })