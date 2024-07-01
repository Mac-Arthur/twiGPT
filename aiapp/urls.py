from django.urls import path
from .import views

urlpatterns = [
    path('',views.index,name='index'),
    path('translate/', views.translate, name='translate'),
    path('old_queries/', views.get_old_queries, name='get_old_queries'),

]