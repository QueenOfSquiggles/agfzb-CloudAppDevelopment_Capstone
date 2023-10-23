from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
# from .restapis import related methods
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json
from djangoapp.models import CarMake, CarModel

from djangoapp.restapis import get_dealer_by_id, get_dealer_reviews_from_cf, get_dealers_from_cf, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)

# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, "djangoapp/contact.html", context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
    return render(request, "djangoapp/registration.html", context)           

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    '''
    Processes registration requests. GET returns the registration page; POST performs a registration and login
    '''
    if request.method == "GET":
        return render(request, "djangoapp/registration.html", {})
    
    if request.method != "POST":
        return redirect("djangoapp:index")
    user_exist = False
    username = request.POST['username']
    password = request.POST['password']
    firstname = request.POST['firstname']
    lastname = request.POST['lastname']
    print(f"Handling registration request {username} :: {firstname} {lastname}")
    try:
        User.objects.get(username=username)
        user_exist = True
    except:
        pass
    if not user_exist:
        user = User.objects.create_user(username=username, password=password, first_name=firstname, last_name=lastname)
        login(request, user)
        return redirect("djangoapp:index")
    return login_request(request) # reuse login code from earlier

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        # isn't it super bad practice to just hard-code the API endpoint in the code? Especially in a public repo???
        # IDGAF, IBM doesn't charge me since it's part of a course. Fuck 'em
        dealerships = get_dealers_from_cf()
        dealer_names = list(map(lambda d: d.short_name, dealerships))
        return render(request, "djangoapp/index.html", context={
            'dealers': dealerships
        })
        # return HttpResponse(dealer_names)

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    reviews = get_dealer_reviews_from_cf(dealer_id)
    dealer = get_dealer_by_id(dealer_id)
    score = 0
    for rev in reviews:
        if rev.sentiment == "positive":
            score += 1
        elif rev.sentiment == "negative":
            score -= 1
            
    return render(request, "djangoapp/dealer_details.html", context={
        "reviews" : reviews,
        "dealer": dealer,
        "score" : score
    })

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...

def add_review(request, dealer_id):
    if request.user.is_authenticated:
        context = {}
        if request.method == "GET":
            context["dealerObj"] = get_dealer_by_id(dealer_id)
            context["dealership"] = dealer_id
            dealer_models =list(CarModel.objects.all())
            dealer_models = filter(lambda d: d.dealer_id == dealer_id, dealer_models)
            context["models"] = dealer_models
            return render(request, "djangoapp/add_review.html", context=context)
        if request.method == "POST":
            
            car_model = CarModel.objects.first()
            car_model_post = request.POST.get("car_model", "")
            if car_model_post != "":
                try:
                    model_id = int(car_model_post)
                    car_model = CarModel.objects.get(id=model_id)
                except CarModel.DoesNotExist as dne:
                    print(f"Car Model {car_model_post} does not exist in DB!! --> {dne}")
                except Exception as e:
                    print(f"Unhandled error during acquisition of car model {car_model_post}! --> {e}")

            payload = {
                "review": {
                    "id" : 0, #what is this id even used for???
                    "time": str(datetime.now().utcnow().isoformat()),
                    # parameters for API
                    "name": request.user.username,
                    "dealership": dealer_id,
                    "review": str(request.POST.get("review", "no review text")),
                    "purchase": bool(request.POST.get("purchase", "False") == "True"),
                    "purchase_date": str(request.POST.get("purchase_date", datetime.now())),
                    "car_make": car_model.car_make.name,
                    "car_model": car_model.name,
                    "car_year": str(car_model.year),
                    "another": "discarded value because this doesn't need to exist LOL"
                }
            }
            print("Adding review from views with payload: ",json.dumps(payload, indent=1))

            post_review(payload=payload)
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
    return redirect("djangoapp:index")

# def debug_print_all_models():
#     models = CarModel.objects.all()
#     for m in models:
#         print(f"\t({m.id}) :: {m}")