from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .models import Post, Category
from django.utils.text import slugify

def send_otp_email(email, otp_code, role):
    # Customize message based on user role
    role_name = {
        'STAFF': 'Staff/Admin',
        'TECHNICAL': 'Technical Official',
        'REGULAR': 'Regular User'
    }.get(role, 'User')
    
    subject = f"Your OTP Code for {role_name} Verification"
    message = f"""
    Hello,

    Your One-Time Password (OTP) for verifying your {role_name} account is:

    🔐 {otp_code}

    This OTP will expire in 30 minutes.

    If you did not request this, please ignore this email. 

    Best regards,  
    News Blog Team
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False

def login_request(request):
    if request.user.is_authenticated:
        # Redirect to appropriate dashboard based on role
        if request.user.role == 'STAFF':
            return redirect('staff_dashboard')
        elif request.user.role == 'TECHNICAL':
            return redirect('technical_dashboard')
        else:
            return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            
            # Generate and send OTP
            otp = user.generate_otp()
            send_otp_email(email, otp, user.role)
            
            # Store user info in session
            request.session['otp_user_id'] = user.id
            request.session['otp_user_role'] = user.role
            
            return redirect('verify_otp')
                
        except User.DoesNotExist:
            messages.error(request, "No account found with this email. Please sign up first.")
    
    return render(request, 'signin.html')

def verify_otp(request):
    if 'otp_user_id' not in request.session:
        return redirect('login_request')
    
    user_id = request.session['otp_user_id']
    user_role = request.session.get('otp_user_role', 'REGULAR')
    
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            otp_entered = request.POST.get('otp')
            
            # OPTION 1: Simple solution without custom backend
            if user.verify_otp(otp_entered):
                # Manually set the backend and log in
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                # Clear session data
                del request.session['otp_user_id']
                if 'otp_user_role' in request.session:
                    del request.session['otp_user_role']
                
                # Redirect based on role
                if user.role == 'STAFF':
                    return redirect('staff_dashboard')
                elif user.role == 'TECHNICAL':
                    return redirect('technical_dashboard')
                else:
                    return redirect('index')
            else:
                messages.error(request, "Invalid or expired OTP")
    
    except User.DoesNotExist:
        messages.error(request, "User account not found.")
        return redirect('login_request')
    
    return render(request, 'verify_otp.html', {'role': user_role})




def resend_otp(request):
    if 'otp_user_id' not in request.session:
        return redirect('login_request')
    
    user_id = request.session['otp_user_id']
    user_role = request.session.get('otp_user_role', 'REGULAR')
    
    try:
        user = User.objects.get(id=user_id)
        otp = user.generate_otp()
        send_otp_email(user.email, otp, user_role)
        messages.success(request, "New OTP sent to your email")
    except User.DoesNotExist:
        messages.error(request, "User account not found.")
    
    return redirect('verify_otp')