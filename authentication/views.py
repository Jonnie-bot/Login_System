from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from login_system import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token

# Create your views here.


def home(request):
    return render(request, 'index.html')


def signup(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        # username = request.POST.['username'] => this can be used to
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        password = request.POST.get('pass1')
        confirm_password = request.POST.get('pass2')

        if User.objects.filter(username=username):
            messages.error(request, 'Username is already in use.')
            return redirect('home')

        if User.objects.filter(email=email):
            messages.error(request, 'Email is already in use.')
            return redirect('home')

        if len(username) > 10:
            messages.error(request, 'Username must be under 10 characters.')
            return redirect('home')

        if password != confirm_password:
            messages.error(request, 'Password missmatch!')

        if not username.isalnum():
            messages.error(request, 'Username must be alphanumeric')
            return redirect('home')

        myuser = User.objects.create_user(username, email, password)
        myuser.firstname = firstname
        myuser.lastname = lastname
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your account was successfully created. We have sent you a confirmation email, please confirm from your email in order to activate your account.")

        #Welcome Email
        subject = "Welcome to (website name)."
        message = f"Hello {myuser.firstname}!!\n Welcome to (website name)\n Thank you for visiting us \n We've sent a confirmation email, please confirm your email address so as to activate your account.\n\n Thank you\n (the person creating an account)"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        #Confirmation string in Email

        current_site = get_current_site(request)
        email_subject = "Confirm your email (website name)"
        message2 = render_to_string("email_confirmation.html",{
            "name": myuser.firstname,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser),
        })
        email = EmailMessage(
            email_subject, 
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()


        return redirect('signin')

    return render(request, 'signup.html')


def signin(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['pass1']

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            firstname = user.first_name
            return render(request, 'index.html', {'firstname': firstname})
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('home')

    return render(request, 'signin.html')


def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully.")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')
    else:
        return render(request, 'activation_failed.html')    

