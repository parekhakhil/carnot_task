from datetime import datetime
from django.shortcuts import render
from app.serializers import (
    DeviceDataSerializer,
    FileUploadSerializer,
)
from .models import Device, DeviceData
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FileUploadParser, FormParser
import csv
from rest_framework.response import Response
import traceback
from django.core.files.storage import default_storage
from django.conf import settings
import os
from rest_framework import status
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page

# Create your views here.

#Class for reading the csv data
class ReadCSVView(APIView):
    parser_classes = [MultiPartParser, FileUploadParser, FormParser]
    # def get(self, request,*args,**kwargs):

    def post(self, request, *args, **kwargs):
        # if not request.POST._mutable:
        #     request.POST._mutable = True
        file_serializer = FileUploadSerializer(data=request.data)
        device_data = []
        try:
            if file_serializer.is_valid():
                file = request.FILES.get("file")
                filename = default_storage.save(file.name, file)
                f = default_storage.open(
                    os.path.join(settings.MEDIA_ROOT, filename), "r"
                )
                reader = csv.reader(f)
                next(reader, None)
                data = sorted(reader, key=lambda row: row[4], reverse=True)
                for row in data:
                    device, device_created = Device.objects.get_or_create(
                        device_fk=row[0]
                    )
                    _, data_created = DeviceData.objects.get_or_create(
                        device=device,
                        latitude=row[1],
                        longitude=row[2],
                        time_stamp=row[3],
                        sts=row[4],
                        speed=row[5],
                    )
                    device_data.append(_)
            serializer = DeviceDataSerializer(device_data, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Data populated easily!!!",
                    "error": "",
                    "data": serializer.data,
                }
            )
        except Exception as e:
            print(traceback.format_exc())
            return Response(
                {
                    "status": False,
                    "err": {"error": str(e), "msg": "Something went wrong"},
                }
            )


def get_device_info(device_id=None):
    if device_id:
        device_info = DeviceData.objects.filter(device__device_fk=device_id).order_by(
            "-sts"
        )
        return device_info
    else:
        return DeviceData.objects.all()


class DeviceLatestInfoView(APIView):
    def get(self, request, *args, **kwargs):
        deviceid = request.GET.get("deviceid")
        if deviceid:
            if cache.get(deviceid):
                data = cache.get(deviceid)
            else:
                data = get_device_info(device_id=deviceid)
                data = DeviceDataSerializer(
                    data,
                    many=True,
                    fields=(
                        "id",
                        "longitude",
                        "latitude",
                        "speed",
                        "sts",
                        "time_stamp",
                    ),
                ).data
                cache.set(deviceid, data)
            return Response(
                {"status": True, "data": data, "msg": "Data successfully retrieved!"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": False,
                "data": {},
                "err": {"msg": "Enter device id", "error": "No device id found"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )


class LocationRetriveView(APIView):
    def get(self, request, *args, **kwargs):
        deviceid = request.GET.get("deviceid")
        if deviceid:
            loc = "location_{0}".format(deviceid)
            if cache.get(loc):
                data = cache.get(loc)
            else:
                start_point = (
                    get_device_info()
                    .order_by("longitude")
                    .order_by("latitude")
                    .values("latitude", "longitude")
                    .first()
                )
                end_point = (
                    get_device_info()
                    .order_by("longitude")
                    .order_by("latitude")
                    .values("latitude", "longitude")
                    .last()
                )

                data = {
                    "start_location": (
                        start_point["latitude"],
                        start_point["longitude"],
                    ),
                    "end_location": (end_point["latitude"], end_point["longitude"]),
                }
                cache.set(loc, data)
            return Response(
                {
                    "status": True,
                    "data": data,
                    "msg": "Location successfully retrieved",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": False,
                "err": {"error": "Device id not found", "msg": "Something went wrong"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )


class TimeBetweenDataView(APIView):
    def get(self, request, *args, **kwargs):
        device_id = request.GET.get("deviceid")
        start_time = request.GET.get("start")
        end_time = request.GET.get("end")
        try:
            time = "device_{0}_timely_data".format(device_id)
            if cache.get(time) and (
                start_time == cache.get(time)["start_time"]
                and end_time == cache.get(time)["end_time"]
            ):
                # retrived_data = cache.get(time)
                # cache_start_time = retrived_data["start_time"]
                # cache_end_time = retrived_data["end_time"]
                # print('here i am')
                # data = []
                # if start_time == cache_start_time and end_time == cache_end_time:
                print("Here")
                # print(retrived_data['data'])
                data = cache.get(time)["data"]
            else:
                processed_start_time = datetime.strptime(
                    start_time, "%Y-%m-%dT%H:%M:%S%z"
                )
                processed_end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z")
                device_data = DeviceData.objects.filter(
                    device__device_fk=device_id,
                    time_stamp__range=[processed_start_time, processed_end_time],
                )
                data = DeviceDataSerializer(
                    device_data,
                    many=True,
                    fields=("id", "time_stamp", "sts", "latitude", "longitude"),
                ).data
                cache_data = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "data": data,
                }
                cache.set(time, cache_data)
            return Response(
                {
                    "status": True,
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    "status": False,
                    "data": {},
                    "err": {"msg": "Something went wrong", "error": str(e)},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
