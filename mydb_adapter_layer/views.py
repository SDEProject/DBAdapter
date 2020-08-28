import requests
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

# Create your views here.
from django.views import View
from requests import Response
from rest_framework import viewsets, mixins
from travelando import settings
import json


class ResultView(View):
    def retrieve_result_information(self, result, context):
        accomodationenum = result['accommodationenum']
        accomodation_type = accomodationenum.split("#")

        information_result = {"name": result["name"], "accommodation_type": accomodation_type[1],
                              "start_hour": result["starthour"],
                              "end_hour": result["endhour"], "lat_1": result['lat']['#text'],
                              "long_1": result['lon']['#text'],
                              "lat_2": 0, "long_2": 0, "stars": 5, "type": context['subject']}

        if context['subject'] == "":
            information_result['lat_2'] = 0
            information_result['long_2'] = 0

        return information_result

    def retrieve_address_information(self, result):
        provinceenum = result['province']
        province = provinceenum.split("#")

        address = {"city": "Trento", "street": result["street"], "number": result['number'],
                   "province": province[1]}

        print(f'address: {address}')
        return address

    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        context = parameters['context']
        request_parameters = parameters['request_parameters']

        context['query'] = parameters['query']

        response_kg = requests.get(
            f"http://{settings.SERVICE_KNOWLEDGE_HOST}:{settings.SERVICE_KNOWLEDGE_PORT}/{settings.SERVICE_KNOWLEDGE}/queries",
            context)

        response_content = response_kg.content.decode('utf-8')
        json_results = json.loads(response_content)
        results = json_results['results']

        if results:
            json_results = []
            json_address = []
            for result in results:
                json_results.append(self.retrieve_result_information(result, context))
                print(f"ADDRESS {result}")
                json_address.append(self.retrieve_address_information(result))
            response = {
                "results": json_results,
                "addresses": json_address
            }
            return JsonResponse(response, status=response_kg.status_code)
        else:
            response = HttpResponseNotFound("No results found to save!")
            return HttpResponseNotFound(response)