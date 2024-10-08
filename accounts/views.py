from django.shortcuts import render, HttpResponse, redirect
from .forms import *
from .models import Account
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# verification email imports
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail

from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number       
            user.save()

            current_site = get_current_site(request)
            mail_subject = " Please Active Your Account"
            message = render_to_string('accounts/account_verification_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),

            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, "Account Creating Successful, Please Verify your Account")       
            return redirect('signin')

    else:  
        form = AccountForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/account.html', context)



def signin(request):
    if request.method=="POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    # getting the product variation by cart id

                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                        #item.save()
                cart_item = CartItem.objects.filter(user=user)
                ex_var_list = []
                id = []
                for item in cart_item:
                    existing_variation = item.variations.all()
                    ex_var_list.append(list(existing_variation))
                    id.append(item.id)
                for pr in product_variation:
                    if pr in ex_var_list:
                        index = ex_var_list.index(pr)
                        item_id = item[index]
                        item = CartItem.objects.get(id=item_id)
                        item.quantity += 1 
                        item.user = user
                        item.save()
                    else:
                        cart_item = CartItem.objects.filter(cart=cart)
                        for item in cart_item:
                            item.user = user
                            item.save()


            except:
                pass
            
            auth.login(request, user)
            messages.success(request, "logged in successfully")
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query 
            #    print('query -->',query)   
                # next = /cart/checkout/
                params = dict(x.split('-') for x in query.split('&'))
            #    print('params -->',params)
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
                
            except:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid Login Creadentials")
            return redirect('signin')
    
    return render(request, 'accounts/signin.html')

@login_required(login_url = 'signin')
def signout(request):
    auth.logout(request)
    messages.success(request, 'You are Successfully Logged Out, Hope you come back soon')
    return redirect ('home')

def activate(request, uidb64, token):
    try:   
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True 
        user.save()
        messages.success(request, "Congratulation  !! Account Verified Successfully")
        return redirect('login')
    else:
        messages.error(request, "Invalid Activation Link")
        return redirect('signup')


@login_required(login_url = 'signin')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.get(email=email).exists():
            user = Account.object.get(email_exact=email)

            current_site = get_current_site(request)
            mail_subject = " Please Reset Your Password"
            message = render_to_string('accounts/reset_password_email.html',{
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),

            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            messages.success(request, " Password Reset Email Successfully Send")
            send_email.send()

            messages.success(request, "Password Reset Email to your email Address")
            return redirect('signin')

        else:
            message.error(request, "Account Doesnot Exists")
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')

def resetPassword_validate(request):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] =  uid 
        message.success(request, 'Please Reset Your Password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This Link has Expired')
        return redirect('login')
    
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password Reset Successfully')
            return redirect('signin')
        else:
            messages.error(request, 'Password Does Not Match')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')
