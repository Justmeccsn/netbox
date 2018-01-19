from __future__ import unicode_literals

import threading

from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse

from extras.models import CustomAnonymous


BASE_PATH = getattr(settings, 'BASE_PATH', False)
LOGIN_REQUIRED = getattr(settings, 'LOGIN_REQUIRED', False)


class LoginRequiredMiddleware(object):
    """
    If LOGIN_REQUIRED is True, redirect all non-authenticated users to the login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if LOGIN_REQUIRED and not request.user.is_authenticated():
            # Redirect unauthenticated requests to the login page. API requests are exempt from redirection as the API
            # performs its own authentication.
            api_path = reverse('api-root')
            if not request.path_info.startswith(api_path) and request.path_info != settings.LOGIN_URL:
                return HttpResponseRedirect('{}?next={}'.format(settings.LOGIN_URL, request.path_info))
        return self.get_response(request)


class APIVersionMiddleware(object):
    """
    If the request is for an API endpoint, include the API version as a response header.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_path = reverse('api-root')
        response = self.get_response(request)
        if request.path_info.startswith(api_path):
            response['API-Version'] = settings.REST_FRAMEWORK_VERSION
        return response


class GlobalUserMiddleware(object):
    """
    Retrieve the user from request.
    """
    _user = {}

    @classmethod
    def user(cls):
        try:
            return cls._user[threading.current_thread()]
        # Not instanced
        except KeyError:
            return CustomAnonymous()

    @classmethod
    def set_user(cls, user):
        cls._user[threading.current_thread()] = user

    @classmethod
    def clean_thread(cls):
        cls._user.pop(threading.current_thread(), None)

    def __init__(self, next_layer=None):
        self.get_response = next_layer

    def process_request(self, request):
        self.set_user(request.user)

    def process_response(self, request, response):
        self.clean_thread()
        return response

    def process_exception(self, request, exception):
        self.clean_thread()
        raise exception

    def __call__(self, request):
        response = self.process_request(request)
        if response is None:
            response = self.get_response(request)
        response = self.process_response(request, response)
        return response
