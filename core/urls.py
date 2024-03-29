"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

from core.settings import MEDIA_URL, MEDIA_ROOT
from chat.views import login_view, signup_view, login_required_view, account_settings

urlpatterns = [
    path("", login_view, name="index-page"),
    path("login-required", login_required_view, name="login-required"),
    # path('reg', SignUpView.as_view(), name='reg-page'),
    path("reg", signup_view, name="reg-page"),
    path("chat/", include("chat.urls")),
    path("account-settings", account_settings, name="account-settings"),
    path("admin/", admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
