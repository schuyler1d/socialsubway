from django.shortcuts import redirect, render
from django.conf import settings

from social.exceptions import AuthAlreadyAssociated, AuthException, \
    AuthForbidden


def redirect_to_googleauth2(request):
    #used to redirect content for admin
    if request.user \
       and not request.user.is_anonymous() \
       and not request.user.is_staff:
        
        return render(request, 'noaccess.html', {})
    return redirect('/login/google-oauth2/?approval_prompt=force')


def require_social_staff(backend, details, user, *args, **kwargs):
    whitelist = getattr(settings, 'SOCIAL_STAFF_WHITELIST', {}).get(backend.name, {})
    print (details)
    for key in whitelist.keys():
        if key in details and details[key] in whitelist[key]:
            if user and not user.is_staff:
                user.is_staff = True
                perms = getattr(settings, 'STAFF_DEFAULT_PERMS', [])
                if perms:
                    from django.contrib.auth.models import Permission
                    for p in Permission.objects.filter(name__in=perms):
                        user.user_permissions.add(p)
                user.save()
            return
    raise AuthForbidden(backend)
