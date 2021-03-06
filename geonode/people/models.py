# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.db import models
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AbstractUser
from django.db.models import signals
from django.conf import settings

from taggit.managers import TaggableManager
from avatar.templatetags.avatar_tags import avatar_url
from avatar.models import Avatar

from geonode.base.enumerations import COUNTRIES
from geonode.groups.models import GroupProfile

from account.models import EmailAddress

from .utils import format_address

if 'notification' in settings.INSTALLED_APPS:
    from notification import models as notification
    
class Profile(AbstractUser):

    """Fully featured Geonode user"""
    # Mapstory stuff
    Volunteer_Technical_Community = models.BooleanField(_('Volunteer Technical Community'),
        help_text=_('indicates membership of the Volunteer Technical Comunity'),
        default=False)
    social_twitter = models.CharField(_('Twitter Handle'), help_text=_('Provide your Twitter handle or URL'), max_length=255, null=True, blank=True)
    social_facebook = models.CharField(_('Facebook Profile'), help_text=_('Provide your Facebook handle or URL'), max_length=255, null=True, blank=True)
    social_github = models.CharField(_('GitHub Profile'), help_text=_('Provide your GitHub handle or URL'), max_length=255, null=True, blank=True)
    social_linkedin = models.CharField(_('LinkedIn Profile'), help_text=_('Provide your LinkedIn handle or URL'), max_length=255, null=True, blank=True)
    education = models.TextField(_('Education'), null=True, blank=True, help_text=_('Provide some details about your Education and Background'))
    expertise = models.TextField(_('Expertise'), null=True, blank=True, help_text=_('Provide some details about your Expertise'))
    
    # End mapstory stuff
    organization = models.CharField(
        _('Organization Name'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('name of the responsible organization'))
    profile = models.TextField(_('Profile'), null=True, blank=True, help_text=_('Introduce yourself in under 200 characters'))
    position = models.CharField(
        _('Position Name'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('role or position of the responsible person'))
    voice = models.CharField(_('Voice'), max_length=255, blank=True, null=True, help_text=_(
        'telephone number by which individuals can speak to the responsible organization or individual'))
    fax = models.CharField(_('Facsimile'), max_length=255, blank=True, null=True, help_text=_(
        'telephone number of a facsimile machine for the responsible organization or individual'))
    delivery = models.CharField(
        _('Delivery Point'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('physical and email address at which the organization or individual may be contacted'))
    city = models.CharField(
        _('City'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('What city do you spend most of your time in?'))
    area = models.CharField(
        _('Administrative Area'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('state, province of the location'))
    zipcode = models.CharField(
        _('Postal Code'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('ZIP or other postal code'))
    country = models.CharField(
        choices=COUNTRIES,
        max_length=3,
        blank=True,
        null=True,
        help_text=_('What country do you spend most of your time in?'))
    keywords = TaggableManager(_('keywords'), blank=True, help_text=_(
        'commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject \
            (space or comma-separated'), related_name='profile_keywords')
    avatar_100 = models.CharField(max_length=512, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('profile_detail', args=[self.username, ])

    def __unicode__(self):
        return u"%s" % (self.username)

    def class_name(value):
        return value.__class__.__name__

    USERNAME_FIELD = 'username'

    def group_list_public(self):
        return GroupProfile.objects.exclude(access="private").filter(groupmember__user=self)

    def group_list_all(self):
        return GroupProfile.objects.filter(groupmember__user=self)

    def keyword_list(self):
        """
        Returns a list of the Profile's keywords.
        """
        return [kw.name for kw in self.keywords.all()]

    def keyword_slug_list(self):
        return [kw.slug for kw in self.keywords.all()]

    @property
    def name_long(self):
        if self.first_name and self.last_name:
            return '%s %s (%s)' % (self.first_name, self.last_name, self.username)
        elif (not self.first_name) and self.last_name:
            return '%s (%s)' % (self.last_name, self.username)
        elif self.first_name and (not self.last_name):
            return '%s (%s)' % (self.first_name, self.username)
        else:
            return self.username

    @property
    def location(self):
        return format_address(self.delivery, self.zipcode, self.city, self.area, self.country)


def get_anonymous_user_instance(Profile):
    return Profile(username='AnonymousUser')


def profile_post_save(instance, sender, **kwargs):
    """Make sure the user belongs by default to the anonymous group.
    This will make sure that anonymous permissions will be granted to the new users."""
    from django.contrib.auth.models import Group
    anon_group, created = Group.objects.get_or_create(name='anonymous')
    instance.groups.add(anon_group)
    # keep in sync Profile email address with Account email address
    if instance.email not in [u'', '', None] and not kwargs.get('raw', False):
        EmailAddress.objects.filter(user=instance, primary=True).update(email=instance.email)
    Profile.objects.filter(id=instance.id).update(avatar_100=avatar_url(instance, 100))


def email_post_save(instance, sender, **kw):
    if instance.primary:
        Profile.objects.filter(id=instance.user.pk).update(email=instance.email)


def profile_pre_save(instance, sender, **kw):
    matching_profiles = Profile.objects.filter(id=instance.id)
    if matching_profiles.count() == 0:
        return
    if instance.is_active and not matching_profiles.get().is_active and \
            'notification' in settings.INSTALLED_APPS:
        notification.send([instance, ], "account_active")

def avatar_post_save(instance, sender, **kw):
    Profile.objects.filter(id=instance.user.id).update(avatar_100=avatar_url(instance.user, 100))


signals.pre_save.connect(profile_pre_save, sender=Profile)
signals.post_save.connect(profile_post_save, sender=Profile)
signals.post_save.connect(email_post_save, sender=EmailAddress)
signals.post_save.connect(avatar_post_save, sender=Avatar)

