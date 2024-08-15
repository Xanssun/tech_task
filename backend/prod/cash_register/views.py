from collections import Counter

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item


class CashMachineAPIView(APIView):
    def post(self, request):
        item_ids = request.data.get('items', [])
        item_counts = Counter(item_ids)

        total_sum = 0
        item_list = []

        for item_id, quantity in item_counts.items():
            try:
                item = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                continue

            total_cost = item.price * quantity
            total_sum += total_cost
            item_list.append({
                'name': item.title,
                'quantity': quantity,
                'total_cost': f"{total_cost:.2f}"
            })
        
        context = {
            'items': item_list,
            'total_sum': f"{total_sum:.2f}",
            'creation_time': timezone.now().strftime('%d.%m.%Y %H:%M'),
        }

        html = render_to_string('index.html', context)

        return HttpResponse(html)
    

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
