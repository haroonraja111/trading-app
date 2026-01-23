# -------------------------------------------------------#
#------------------------ urls.py-----------------------#
# -------------------------------------------------------#
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path("", home_view, name="home"),

    path("login/", auth_views.LoginView.as_view(template_name="App/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("stocks/", stock_list_view, name="stock_list"),
    path("stocks/add/", stock_create_view, name="stock_add"),
    path("stocks/fetch/", fetch_stock_price_ajax, name="fetch_stock_price"),  # Must be before stocks/<int:pk>/
    path("api/stocks/refresh/", refresh_stock_prices_api, name="refresh_stock_prices"),  # API endpoint for batch price refresh
    path("stocks/<int:pk>/", stock_detail_view, name="stock_detail"),
    path("stocks/<int:pk>/edit/", stock_update_view, name="stock_update"),
    path("stocks/<int:pk>/delete/", stock_delete_view, name="stock_delete"),

    path("trades/", trade_list_view, name="trade_list"),
    path("trades/add/", trade_create_view, name="trade_add"),
    path("trades/<int:pk>/edit/", trade_update_view, name="trade_update"),
    path("trades/<int:pk>/delete/", trade_delete_view, name="trade_delete"),
    path("portfolio/", portfolio_dashboard, name="portfolio_dashboard"),

]
