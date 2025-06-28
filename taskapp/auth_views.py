from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import User



def send_otp_email(email, otp_code):
    subject = "Your OTP Code for Verification"
    message = f"""
    Hello,

    Your One-Time Password (OTP) for verifying your account is:

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
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            
            if not user.is_verified:
                # Generate and send OTP
                otp = user.generate_otp()
                send_otp_email(email, otp)
                
                request.session['otp_user_id'] = user.id
                return redirect('verify_otp')
            
            # Authenticate with password
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Invalid credentials")
                
        except User.DoesNotExist:
            messages.error(request, "Account not found")
    
    return render(request, 'signin.html')

def verify_otp(request):
    if 'otp_user_id' not in request.session:
        return redirect('login_request')
    
    user_id = request.session['otp_user_id']
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        
        if user.verify_otp(otp_entered):
            login(request, user)
            del request.session['otp_user_id']
            return redirect('home')
        else:
            messages.error(request, "Invalid or expired OTP")
    
    return render(request, 'verify_otp.html')

def resend_otp(request):
    if 'otp_user_id' not in request.session:
        return redirect('login_request')
    
    user_id = request.session['otp_user_id']
    user = User.objects.get(id=user_id)
    
    otp = user.generate_otp()
    send_otp_email(user.email, otp)
    
    messages.success(request, "New OTP sent to your email")
    return redirect('verify_otp')