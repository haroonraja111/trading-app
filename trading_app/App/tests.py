from unicodedata import name
from django.test import TestCase
from . models import Stock

class ModelTesting(TestCase):
    def setUp(self):
        self.stock = Stock.objects.create(symbol="TEST", name="Test Company")
    
    def test_stock_model(self):
        d = self.stock
        self.assertTrue(isinstance(d, Stock))
        self.assertEqual(str(d), "TEST")
        