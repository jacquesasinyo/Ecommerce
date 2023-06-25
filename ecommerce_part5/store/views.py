from django.shortcuts import render
from .models import *
from django.http import JsonResponse
import json
import datetime
from .utils import cookieCart,cartData,guestOrder
from django.db.models import Q
from django.core.paginator import Paginator

def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    products = Product.objects.all()
     # Configure the number of items per page
    paginator = Paginator(products, 3)  # Assuming 10 products per page
    
    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')
    
    # Get the Page object for the current page number
    page_obj = paginator.get_page(page_number)
    context = {"products": page_obj,'cartItems':cartItems}
    return render(request, 'store/store.html', context)





def search(request):
    data = cartData(request)
    cartItems = data['cartItems']

    query = request.GET.get('query')
    products = Product.objects.filter(
        Q(name__icontains=query)
    )
    context = {"products": products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']


    context = {'items':items,'order':order,'cartItems':cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items':items,'order':order,'cartItems':cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    print('productId',productId)
    print('action',action)
    customer = request.user.customer
    product = Product.objects.get(id = productId)
    order, created = Order.objects.get_or_create(customer=customer,complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order,product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    orderItem.save()   

    if orderItem.quantity <= 0:
        orderItem.delete()
    return JsonResponse('Item was added',safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete=False)
        
    #create an instance of the shipping address if an address was sent
             
    else:
        customer, order = guestOrder(request,data)
        
    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()   
    if order.shipping == True:
            ShippingAddress.objects.create(
                customer=customer,
                order = order,
                address = data['shipping']['address'],
                city = data['shipping']['city'],
                state = data['shipping']['state'],
                zipcode = data['shipping']['zipcode'],

            )
    return JsonResponse('Payment complete',safe=False)
