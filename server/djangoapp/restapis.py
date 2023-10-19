import re
import string
import requests
import json
# import related models here
from requests.auth import HTTPBasicAuth

from djangoapp.models import CarDealer, DealerReview

# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, params={}, api_key = None, **kwargs):
	print(f"GET from {url}  ::{params}")
	response = {}
	try:
		if api_key:
			# use auth
			response = requests.get(url, headers={'Content-Type': 'application/json'}, params=params, auth=HTTPBasicAuth('api_key', api_key))
		else:
			# no auth needed
			response = requests.get(url, headers={'Content-Type': 'application/json'}, params=params)

		# if response:
		# 	print(f"Got result [{response}]")
		# 	print(f"Data TEXT: '{response.text}'")

		return json.loads(response.text)
	except Exception as e:
		print(f"Error occurred: {response} --> {type(e)}:: {e}")
		return

def post_request(url, json_payload, **kwargs):
	try:
		response = requests.post(url, params=kwargs, json=json_payload)
		return response
	except Exception as e: 
		print(f"Error occurred: {type(e)}::{e}")

# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)


# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(**kwargs):
	results = []
	json_result = get_request("https://us-south.functions.appdomain.cloud/api/v1/web/537e76ff-f3b6-40d4-820e-ae3f863e7ff5/dealership-package/dealership")
	if json_result:
		for dealer in json_result:
			dealer_obj = CarDealer(
				address=dealer["address"],
				city=dealer["city"],
				full_name=dealer["full_name"],
				id=dealer["id"],
				lat=dealer["lat"],
				long=dealer["long"],
				short_name=dealer["short_name"],
				st=dealer["st"],
				zip=dealer["zip"],
			)
			results.append(dealer_obj)
	return results

def get_dealer_by_id(dealer_id):
	dealers = get_dealers_from_cf()
	for d in dealers:
		if d.id == dealer_id:
			return d
	return

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list

def get_dealer_reviews_from_cf(dealer_id):
	results = []
	json_result = get_request("https://us-south.functions.appdomain.cloud/api/v1/web/537e76ff-f3b6-40d4-820e-ae3f863e7ff5/dealership-package/review", params={
		"dealerFilterTargetText": dealer_id
	})
	if json_result:
		if "error" in json_result:
			print(f"Error getting reviews: {json_result}")
			return results
		for data in json_result:
			
			rev = DealerReview(
				data.get("dealership"),
				data.get("name"),
				data.get("purchase"),
				data.get("review"),
				data.get("purchase_date"),
				data.get("car_make"),
				data.get("car_model"),
				data.get("car_year"),
				analyze_sentiment(
					text=data.get("review"),
				),
				data.get("id")
			)

			results.append(rev)
	return results

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative

def analyze_sentiment(**kwargs):

	# again? Shouldn't these be in some kind of keystore??? Why the fuck is this the capstone???
	url = "https://api.us-east.natural-language-understanding.watson.cloud.ibm.com/instances/4a65f437-3160-448b-8e78-f5e4530d5a36/v1/analyze?version=2019-07-12"
	response = requests.post(
		url = url, 
		headers = {
			"Content-Type" : "application/json"
		}, 
		params = {
			"text": kwargs["text"],
			"features": ["sentiment"],
			"return_analyzed_text": False
		}, 
		auth = HTTPBasicAuth("apikey", "AJMHNXKcoAvlGXVRI9BMdOIq8HpQF4EOsYvZrixwK9MB")
	)
	json_data = {}
	try:
		json_data = response.json()
	except:
		pass
	strip = {}
	strip = json_data.get("sentiment", {})
	strip = strip.get("document", {})
	strip = strip.get("label", {})
	if strip == {}:
		return "neutral"
	return str(strip)

def post_review(payload):
	print("Rest API recieved payload: ", json.dumps(payload, indent=1))
	response = post_request(
		url="https://us-south.functions.appdomain.cloud/api/v1/web/537e76ff-f3b6-40d4-820e-ae3f863e7ff5/dealership-package/review", json_payload=payload
	)
	print(f"When posting new review, got response: {response}")
	if response:
		print(response.text)