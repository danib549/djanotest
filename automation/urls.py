from django.urls import path

from. import views
urlpatterns = [
    path('global_settings/', views.global_settings, name='global_settings'),
    path('create_script/', views.create_script, name='create_script'),
    path('scripts/', views.script_list, name='script_list'),
    path('load_script/', views.load_script, name='load_script'),
    path('delete_step/<int:step_id>/', views.delete_step, name='delete_step'),
    path('load_step/<int:step_id>/', views.load_step, name='load_step'),
    path('update_step_order/', views.update_step_order, name='update_step_order'),
    path('get_script_versions/', views.get_script_versions, name='get_script_versions'),
]
