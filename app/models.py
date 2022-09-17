from django.db import models

# Create your models here.


class Device(models.Model):
    device_fk = models.PositiveIntegerField()

    def __str__(self):
        return str(self.device_fk)


class DeviceData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=6, decimal_places=3)
    longitude = models.DecimalField(max_digits=6, decimal_places=3)
    time_stamp = models.DateTimeField()
    sts = models.DateTimeField()
    speed = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.device.device_fk)
