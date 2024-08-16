import os
from collections import Counter
from io import BytesIO

import pdfkit
import qrcode
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.views import APIView

from .models import Item


class CashMachineAPIView(APIView):
    """
    APIView для обработки запросов к кассовому аппарату, который генерирует PDF-чеки 
    на основе списка товаров, переданного в запросе.
    """

    def post(self, request):
        """
        Обрабатывает POST-запрос для генерации PDF-чека.

        Args:
            request (HttpRequest): Запрос, содержащий список товаров.

        Returns:
            JsonResponse: Ответ, содержащий сообщение и URL к сгенерированному PDF-файлу.
        """
        item_counts = self.get_item_counts(request.data.get('items', []))
        item_list, total_sum = self.calculate_totals(item_counts)

        context = self.build_context(item_list, total_sum)
        pdf_file = self.generate_pdf(context)

        file_url = self.save_pdf(pdf_file, request)

        print(file_url) # ссылка которая идет в qr

        qr_code_image = self.generate_qr_code(file_url)

        response = HttpResponse(content_type="image/png")
        response.write(qr_code_image)
        return response

    def get_item_counts(self, item_ids):
        """
        Подсчитывает количество каждого товара в списке.

        Args:
            item_ids (list): Список идентификаторов товаров.

        Returns:
            Counter: Счетчик, содержащий количество каждого товара.
        """
        return Counter(item_ids)

    def calculate_totals(self, item_counts):
        """
        Вычисляет общую сумму и создает список товаров с их количеством и стоимостью.

        Args:
            item_counts (Counter): Счетчик с количеством каждого товара.

        Returns:
            tuple: Список товаров с их количеством и стоимостью, общая сумма.
        """
        total_sum = 0
        item_list = []

        items = Item.objects.filter(id__in=item_counts.keys())
        for item in items:
            quantity = item_counts[item.id]
            total_cost = item.price * quantity
            total_sum += total_cost
            item_list.append({
                'name': item.title,
                'quantity': quantity,
                'total_cost': f"{total_cost:.2f}"
            })

        return item_list, total_sum

    def build_context(self, item_list, total_sum):
        """
        Создает контекст для рендеринга HTML-шаблона.

        Args:
            item_list (list): Список товаров с их количеством и стоимостью.
            total_sum (float): Общая сумма.

        Returns:
            dict: Контекст, содержащий информацию о товарах, общей сумме и времени создания.
        """
        return {
            'items': item_list,
            'total_sum': f"{total_sum:.2f}",
            'creation_time': timezone.now().strftime('%d.%m.%Y %H:%M'),
        }

    def generate_pdf(self, context):
        """
        Генерирует PDF из HTML-шаблона с использованием переданного контекста.

        Args:
            context (dict): Контекст для рендеринга HTML-шаблона.

        Returns:
            bytes: Сгенерированный PDF-файл в виде байтов.
        """
        html = render_to_string('index.html', context)

        options = {
            'page-size': 'Letter',
            'encoding': "UTF-8",
        }
        
        return pdfkit.from_string(html, False, options=options)

    def save_pdf(self, pdf_file, request):
        """
        Сохраняет PDF-файл в файловую систему и возвращает его URL.

        Args:
            pdf_file (bytes): Сгенерированный PDF-файл в виде байтов.
            request (HttpRequest): Текущий запрос для построения абсолютного URL.

        Returns:
            str: Абсолютный URL к сохраненному PDF-файлу.
        """
        pdf_name = f"check_{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf"
        path = os.path.join(settings.MEDIA_ROOT, pdf_name)
        
        with open(path, "wb") as f:
            f.write(pdf_file)

        return request.build_absolute_uri(settings.MEDIA_URL + pdf_name)

    def generate_qr_code(self, file_url):
        """
        Генерирует QR-код с URL к PDF-файлу.

        Args:
            file_url (str): URL к PDF-файлу.

        Returns:
            bytes: Сгенерированный QR-код в виде байтов.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(file_url)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')


        qr_image = BytesIO()
        img.save(qr_image, format='PNG')
        return qr_image.getvalue()
