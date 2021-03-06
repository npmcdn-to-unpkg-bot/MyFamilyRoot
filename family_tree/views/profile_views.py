# encoding: utf-8
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from family_tree.decorators import same_family_required
from family_tree.models.person import GENDER_CHOICES
from custom_user.decorators import set_language
from gallery.models import Tag

import json


def genders(request):
    '''
    Provides JSON response of all genders and localised gender display text
    '''
    response = []

    if request.user != None and request.user.is_authenticated():
        request.session['django_language'] = request.user.language

    for code, display in GENDER_CHOICES:
        response.append({ 'value' : code, 'text' : display.__str__() })

    return HttpResponse(json.dumps(response), content_type="application/json")



@login_required
@same_family_required
def profile(request, person_id = 0, person = None, edit_mode = False):
    '''
    Shows the profile of a person
    '''

    #Cannot enter edit mode if profile is locked
    if request.user.id != person.user_id and person.locked == True:
        edit_mode = False


    if edit_mode:

        #Cannot edit the first language or email of someone else if they are a user
        if not person.user_id:
            show_email_and_language = True
            can_delete= True
        else:
            if request.user.id == person.user_id:
                show_email_and_language = True
            else:
                show_email_and_language = False

            can_delete= False

        return render(request, 'family_tree/edit_profile.html', {
                                    'person' : person,
                                    'languages' : settings.LANGUAGES,
                                    'show_locked': (True if request.user.id == person.user_id else False),
                                    'show_email_and_language' : show_email_and_language,
                                    'can_delete' : can_delete,
                                })
    else:

        invite_allowed = False
        if not person.user_id and person.year_of_death == 0:

            #check no pending invites to email address
            from email_confirmation.models import EmailConfirmation
            try:
                invite = EmailConfirmation.objects.get(person_id = person.id, email_address = person.email)
                if invite.email_address != person.email:
                    invite_allowed = True

            except:
                invite_allowed = True

        return render(request, 'family_tree/profile.html', {
                                    'person' : person,
                                    'languages' : settings.LANGUAGES,
                                    'locked': (True if request.user.id != person.user_id and person.locked else False),
                                    'show_relation_to_me': (True if request.user.id != person.user_id else False),
                                    'invite_allowed' : invite_allowed,
                                    'show_photos': (True if Tag.objects.filter(person_id=person.id).count() > 0 else False),
                                    'has_email': (True if person.email else False),
                                    })


@login_required
@same_family_required
def edit_profile(request, person_id = 0, person = None, requested_language = ''):
    '''
    The form that allows a user to edit the details of a person.  It displays the for and processes it
    '''
    return profile(request, person_id, requested_language, edit_mode = True)




@login_required
@set_language
@same_family_required
def update_person(request, person_id = 0, person = None):
    '''
    This is an API to set the property of a person field
    Expecting POST values of:
        pk: person ID
        name: field name to change
        value: new value
    '''

    if request.method != 'POST':
        return HttpResponse(status=405, content="Only POST requests allowed")

    #Make sure we can't change locked profiles
    if person.locked and person.user_id != request.user.id:
        return HttpResponse(status=405, content="Access denied to locked profile")

    field_name = request.POST.get("name")

    if field_name not in [  'email', 'language','locked',
                            'birth_year','year_of_death','telephone_number',
                            'website','address', 'skype_name',
                            'facebook', 'twitter', 'linkedin',
                            'occupation', 'spoken_languages',
                            'name','gender',]:
        return HttpResponse(status=405, content="Access denied to change confirmed user settings")

    #Check we don't change any settings for a confirmed user
    if person.user_id and field_name in ['email', 'language',]:
        if person.user_id != request.user.id:
            return HttpResponse(status=405, content="Access denied to change confirmed user settings")

    try:
        setattr(person, field_name, request.POST.get("value"))
        person.save()
        return HttpResponse(status=200, content="OK")

    except Exception as e:
        return HttpResponse(status=405, content=e)


@login_required
@set_language
@same_family_required
def delete_profile(request, person_id = 0, person = None):
    '''
    API to delete a person
    '''

    #Cannot delete any profile of a confirmed user
    if person.user_id:
        return HttpResponse(status=405, content="Cannot delete user profile")

    person.delete()

    return HttpResponseRedirect('/')



@login_required
@same_family_required
def edit_biography(request, person_id = 0, person = None):
    '''
    View to edit the biography in a particular language
    '''

    return render(request, 'family_tree/edit_biography.html', {
                                'person' : person
                            })



@login_required
@same_family_required
def update_biography(request, person_id = 0, person = None):
    '''
    API to update biography
    '''

    if person.locked and person.user_id != request.user.id:
        return HttpResponse(status=405, content="Access denied to locked profile")

    person.biography = request.POST.get("biography","")

    person.save()

    return profile(request, person_id)




