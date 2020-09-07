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
        print(f"RESULT COMPLETE: {result}")
        print(f"CONTEXT COMPLETE: {context}")

        if 'lat' in result and 'lon' in result:
            lat = result['lat']
            long = result['lon']
            if type(lat) is dict and type(long) is dict:
                lat_1 = lat["#text"]
                long_1 = long["#text"]
            elif type(lat) is str and type(long) is str:
                lat_1 = lat
                long_1 = long
        elif 'poi_from_lon' in result and 'poi_from_lat' in result and 'poi_to_lon' in result and 'poi_to_lat' in result:
            lat_1 = result['poi_from_lat']
            long_1= result['poi_from_lon']
            lat_2 = result['poi_to_lat']
            long_2 = result['poi_to_lon']
            if type(lat_1) is dict and type(long_1) is dict and type(lat_2) is dict and type(long_2) is dict:
                lat_1 = lat_1["#text"]
                long_1 = long_1["#text"]
                lat_2 = lat_2["#text"]
                long_2 = long_2["#text"]

        information_result = {"name": result["name"], "lat_1": lat_1, "long_1": long_1, "type": context['subject']}

        if context['subject'] == "ActivityPath":
            information_result['lat_2'] = lat_2
            information_result['long_2'] = long_2
            information_result['path_from'] = result['poi_from']
            information_result['path_to'] = result['poi_to']
            information_result['time'] = result['time']['#text']
            information_result['path_length'] = result['length']['#text']

            if 'path_difficulty' in result:
                information_result['path_difficulty'] = result['path_difficulty']
            elif 'path_difficulty' in context:
                information_result['path_difficulty'] = ""
                for difficulty in context['path_difficulty']:
                    information_result['path_difficulty'] += difficulty
                    if len(context['path_difficulty']) == 2:
                        information_result += " and "
                    elif len(context['path_difficulty']) > 2:
                        information_result += ", "
        elif context['subject'] == "hotel":
            accomodationenum = result['accommodationenum']
            accomodation_type = accomodationenum.split("#")

            information_result["accommodation_type"] = accomodation_type[1]
            information_result["start_hour"] = result["starthour"]
            information_result["end_hour"] = result["endhour"]
            #information_result["stars"] =
        elif context['subject'] == 'Shop':
            if 'shop_enum' in result:
                information_result['shop_enum'] = result['shop_enum']
            elif 'shop_enum' in context:
                information_result['shop_enum'] = context['shop_enum']

        return information_result

    def retrieve_address_information(self, result, context):
        print(f"RESULT COMPLETE: {result}")
        print(f"CONTEXT COMPLETE: {context}")
        address = {}

        if context['subject'] != "ActivityPath":
            address = {"street": result["street"], "number": result['number']}

            if "city" in result:
                address["city"] = result["city"]
            else:
                address["city"] = context["comune"]

            if "province" in result:
                provinceenum = result['province']
                province = provinceenum.split("#")

                address["province"] = province[1]
            else:
                address["province"] = context["region"]

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
                json_address.append(self.retrieve_address_information(result, context))
            response = {
                "results": json_results,
                "addresses": json_address
            }
            return JsonResponse(response, status=response_kg.status_code)
        else:
            response = HttpResponseNotFound("No results found to save!")
            return HttpResponseNotFound(response)