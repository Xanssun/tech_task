from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item


class CashMachineAPIView(APIView):
    def post(self, request):
        pass

    def get(self, request):
        items = Item.objects.all()

        item_data = [
            {
                'id': item.id,
                'name': item.title,
                'price': item.price,
            }
            for item in items
        ]

        return Response(item_data, status=status.HTTP_200_OK)
