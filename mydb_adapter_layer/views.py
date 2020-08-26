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
    def get_first_address(self, parameters):
        response = requests.get(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/address", parameters)
        if response.status_code == 200:
            json_response = response.json()
            if json_response:
                return json_response[0]
        return None

    def create_address(self, json):
        response = requests.post(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/address/", None, json)
        return response

    def get_or_create_address(self, json):
        provinceenum = json['province']
        province = provinceenum.split("#")

        address = {"city": "Trento", "street": json["street"], "number": json['number'],
                   "province": province[1]}

        print(f'address: {address}')
        '''
        address = {"city": json["city"], "street": json["street"], "number": json["number"],
                   "province": json["province"]}
        '''
        response = self.get_first_address(address)
        print(f"get first result: {response}")
        if not response:
            address_response = self.create_address(address)
            if address_response.status_code == 201:
                response = address_response.json()
        return response

    def create_new_result(self, json, address_id):
        json["address"] = address_id
        response = requests.post(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/result/", None, json)
        return response

    def get_result(self, parameters):
        response = requests.get(f"http://{settings.MYDB_HOST}:{settings.MYDB_PORT}/{settings.SERVICE_MYDB_DATA_LAYER}/result", parameters)
        return response

    def create_single_result(self, result, context):
        print(result)

        accomodationenum = result['accommodationenum']
        accomodation_type = accomodationenum.split("#")
        print(accomodation_type)

        information_result = {"name": result["name"], "accommodation_type": accomodation_type[1], "start_hour": result["starthour"],
                              "end_hour": result["endhour"], "lat_1": result['lat']['#text'], "long_1": result['lon']['#text'],
                              "lat_2": 0, "long_2": 0, "stars": 5, "type": context['subject']}

        if context['subject'] == "":
            information_result['lat_2'] = 0
            information_result['long_2'] = 0

        print(information_result)

        '''
        information_result = {"name": result["name"], "accommodation_type": result["accomodation_type"],
                  "description": result["description"],
                  "lat": result["lat"], "long": result["long"], "stars": result["stars"],
                  "type": result["type"]}
        '''

        response = self.get_result(information_result)
        response_content = response.content.decode('utf-8')
        response_json = json.loads(response_content)
        if not response_json:
            address = self.get_or_create_address(result)
            print(f"address {address}")
            if address:
                response = self.create_new_result(information_result, address["id"])
        print(f"response code: {response.status_code}")
        return response

    # 1. Check if the address already exists, then in negative case it creates the address. Otherwise get the id.
    def post(self, request):
        body = request.body.decode('utf-8')
        parameters = json.loads(body)

        context = parameters['context']
        request_parameters = parameters['request_parameters']

        context['query'] = parameters['query']
        ordinal = request_parameters['ordinal']

        response_kg = requests.get(
            f"http://{settings.SERVICE_KNOWLEDGE_HOST}:{settings.SERVICE_KNOWLEDGE_PORT}/{settings.SERVICE_KNOWLEDGE}/queries",
            context)

        response_content = response_kg.content.decode('utf-8')
        json_results = json.loads(response_content)
        results = json_results['results']

        print(results)

        if results:
            if ordinal:
                if ordinal != "last":
                    index = int(ordinal)
                    result = results[index - 1]
                else:
                    last = len(results) - 1
                    result = results[last]
                response = self.create_single_result(result, context)
            else:
                status_code = []
                for result in results:
                    response = self.create_single_result(result, context)
                    status_code.append(response.status_code)
                if 201 in status_code:
                    response.status_code = 201

            return JsonResponse(response.json(), status=response.status_code)
        else:
            response = HttpResponseNotFound("No results found to save!")

            return HttpResponseNotFound(response)
