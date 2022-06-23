from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder


def store(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.htm', context)


def cart(request):

	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.htm', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.htm', context)

def register(request):
	if request.method == "POST":
		#username = request.POST.get('username')
		username = request.POST['username']
		fname = request.POST['fname']
		lname = request.POST['lname']
		email = request.POST['email']
		pass1 = request.POST['pass1']
		pass2 = request.POST['pass2']

		customer = User.objects.create_user(username, email, pass1)
		customer.first_name = fname
		customer.last_name = lname
		customer.save()

		messages.success(request, "Your Account iscreated successfully")

		return redirect('/login')


	return render(request,'store/register.htm')

def login(request):
	if request.method == "POST":
		username = request.POST['username']
		pass1 = request.POST['pass1']

		user= authenticate(username=username, password=pass1)
        
		if user is not None:
			login(request, user)
			
		else:
			messages.error(request, "Bad credentials")
			return redirect('store')
	return render(request,'store/login.htm')

def logout(request):
	pass

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)