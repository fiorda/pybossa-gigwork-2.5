# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from flask import current_app
from flask import request
from flask.ext.babel import lazy_gettext
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from wtforms import IntegerField, DecimalField, TextField, BooleanField, \
    SelectField, validators, TextAreaField, PasswordField, FieldList, SelectMultipleField
from wtforms import SelectMultipleField
from wtforms.fields.html5 import EmailField, URLField
from wtforms.widgets import HiddenInput

import validator as pb_validator
from pybossa import util
from pybossa.core import project_repo, user_repo, task_repo
from pybossa.core import uploader
from pybossa.uploader import local
from flask import safe_join
from flask.ext.login import current_user
import os
from pybossa.forms.fields.time_field import TimeField
from pybossa.sched import sched_variants
from validator import TimeFieldsValidator
from pybossa.core import enable_strong_password
from pybossa.uploader.s3_uploader import s3_upload_file_storage

EMAIL_MAX_LENGTH = 254
USER_NAME_MAX_LENGTH = 35
USER_FULLNAME_MAX_LENGTH = 35
PROJECT_PWD_MIN_LEN = 5


### Forms for projects view

class ProjectForm(Form):
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(project_repo.get_by, 'name',
                                          message=lazy_gettext("Name is already taken."))])
    short_name = TextField(lazy_gettext('Short Name'),
                           [validators.Required(),
                            pb_validator.NotAllowedChars(),
                            pb_validator.Unique(project_repo.get_by, 'short_name',
                                message=lazy_gettext(
                                    "Short Name is already taken.")),
                            pb_validator.ReservedName('project', current_app)])
    long_description = TextAreaField(lazy_gettext('Long Description'),
                                     [validators.Required()])
    description = TextAreaField(lazy_gettext('Description'),
                                [validators.Length(max=255)])
    password = TextField(
                    lazy_gettext('Password'),
                    [validators.Required(),
                        pb_validator.CheckPasswordStrength(
                                        min_len=PROJECT_PWD_MIN_LEN,
                                        special=False)])


class ProjectUpdateForm(ProjectForm):
    id = IntegerField(label=None, widget=HiddenInput())
    description = TextAreaField(lazy_gettext('Description'),
                            [validators.Required(
                                message=lazy_gettext(
                                    "You must provide a description.")),
                             validators.Length(max=255)])
    long_description = TextAreaField(lazy_gettext('Long Description'))
    allow_anonymous_contributors = BooleanField(lazy_gettext('Allow Anonymous Contributors'))
    category_id = SelectField(lazy_gettext('Category'), coerce=int)
    hidden = BooleanField(lazy_gettext('Hide?'))
    email_notif = BooleanField(lazy_gettext('Email Notifications'))
    password = TextField(
                    lazy_gettext('Password'),
                    [validators.Optional(),
                        pb_validator.CheckPasswordStrength(
                                        min_len=PROJECT_PWD_MIN_LEN,
                                        special=False)])
    webhook = TextField(lazy_gettext('Webhook'),
                        [pb_validator.Webhook()])
    sync_target_url = TextField(lazy_gettext('Target URL'))
    sync_target_key = TextField(lazy_gettext('API Key'))
    sync_enabled = BooleanField(lazy_gettext('Enable Project Syncing'))


class ProjectSyncForm(Form):
    target_url = TextField(lazy_gettext('Target URL'))
    target_key = TextField(lazy_gettext('API Key'))


class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('')


class TaskRedundancyForm(Form):
    n_answers = IntegerField(lazy_gettext('Redundancy'),
                             [validators.Required(),
                              validators.NumberRange(
                                  min=task_repo.MIN_REDUNDANCY,
                                  max=task_repo.MAX_REDUNDANCY,
                                  message=lazy_gettext(
                                      'Number of answers should be a \
                                       value between {} and {:,}'.format(
                                          task_repo.MIN_REDUNDANCY,
                                          task_repo.MAX_REDUNDANCY
                                      )))])


class TaskPriorityForm(Form):
    task_ids = TextField(lazy_gettext('Task IDs'),
                         [validators.Required(),
                          pb_validator.CommaSeparatedIntegers()])

    priority_0 = DecimalField(lazy_gettext('Priority'),
                              [validators.NumberRange(
                                  min=0, max=1,
                                  message=lazy_gettext('Priority should be a \
                                                       value between 0.0 and 1.0'))])


class TaskTimeoutForm(Form):
    minimum = 5
    maximum = 120
    msg = 'Timeout should be a value between {} and {}'.format(minimum,
                                                               maximum)
    timeout = IntegerField(lazy_gettext('Timeout in minutes, from {} to {} (default 60)'
                                        .format(minimum, maximum)),
                              [validators.Required(),
                              validators.NumberRange(
                                  min=minimum, max=maximum,
                                  message=lazy_gettext(msg))])


class TaskSchedulerForm(Form):
    _translate_names = lambda variant: (variant[0], lazy_gettext(variant[1]))
    _choices = map(_translate_names, sched_variants())
    sched = SelectField(lazy_gettext('Task Scheduler'), choices=_choices)

    @classmethod
    def update_sched_options(cls, new_options):
        _translate_names = lambda variant: (variant[0], lazy_gettext(variant[1]))
        _choices = map(_translate_names, new_options)
        cls.sched.kwargs['choices'] = _choices


class AnnouncementForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    title = TextField(lazy_gettext('Title'),
                     [validators.Required(message=lazy_gettext(
                                    "You must enter a title for the post."))])
    body = TextAreaField(lazy_gettext('Body'),
                           [validators.Required(message=lazy_gettext(
                                    "You must enter some text for the post."))])

class BlogpostForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    title = TextField(lazy_gettext('Title'),
                     [validators.Required(message=lazy_gettext(
                                    "You must enter a title for the post."))])
    body = TextAreaField(lazy_gettext('Body'),
                           [validators.Required(message=lazy_gettext(
                                    "You must enter some text for the post."))])
    published = BooleanField(lazy_gettext('Publish'))


class PasswordForm(Form):
    password = PasswordField(lazy_gettext('Password'),
                        [validators.Required(message=lazy_gettext(
                                    "You must enter a password"))])


class BulkTaskCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='csv')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    csv_url = TextField(lazy_gettext('URL'),
                        [validators.Required(message=msg_required),
                         validators.URL(message=msg_url)])

    def get_import_data(self):
        return {'type': 'csv', 'csv_url': self.csv_url.data}


class BulkTaskGDImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='gdocs')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    googledocs_url = TextField(lazy_gettext('URL'),
                               [validators.Required(message=msg_required),
                                   validators.URL(message=msg_url)])

    def get_import_data(self):
        return {'type': 'gdocs', 'googledocs_url': self.googledocs_url.data}


class BulkTaskLocalCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='localCSV')
    _allowed_extensions = set(['csv'])
    def _allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in self._allowed_extensions

    def _container(self):
        return "user_%d" % current_user.id

    def _upload_path(self):
        container = self._container()
        filepath = None
        if isinstance(uploader, local.LocalUploader):
            filepath = safe_join(uploader.upload_folder, container)
            if not os.path.isdir(filepath):
                os.makedirs(filepath)
            return filepath

        current_app.logger.error('Failed to generate upload path {0}'.format(filepath))
        raise IOError('Local Upload folder is missing: {0}'.format(filepath))

    def get_import_data(self):
        if request.method == 'POST':
            if 'file' not in request.files:
                return {'type': 'localCSV', 'csv_filename': None}
            csv_file = request.files['file']
            if csv_file.filename == '':
                return {'type': 'localCSV', 'csv_filename': None}
            if csv_file and self._allowed_file(csv_file.filename):
                path = "{0}".format(current_user.id)
                s3_url = s3_upload_file_storage(
                            current_app.config.get("S3_IMPORT_BUCKET"),
                            csv_file,
                            directory=path,
                            file_type_check=False)
                return {'type': 'localCSV', 'csv_filename': s3_url}
        return {'type': 'localCSV', 'csv_filename': None}


class BulkTaskEpiCollectPlusImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='epicollect')
    msg_required = lazy_gettext("You must provide an EpiCollect Plus "
                                "project name")
    msg_form_required = lazy_gettext("You must provide a Form name "
                                     "for the project")
    epicollect_project = TextField(lazy_gettext('Project Name'),
                                   [validators.Required(message=msg_required)])
    epicollect_form = TextField(lazy_gettext('Form name'),
                                [validators.Required(message=msg_required)])

    def get_import_data(self):
        return {'type': 'epicollect',
                'epicollect_project': self.epicollect_project.data,
                'epicollect_form': self.epicollect_form.data}


class BulkTaskFlickrImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='flickr')
    msg_required = lazy_gettext("You must provide a valid Flickr album ID")
    album_id = TextField(lazy_gettext('Album ID'),
                         [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {'type': 'flickr', 'album_id': self.album_id.data}


class BulkTaskDropboxImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='dropbox')
    files = FieldList(TextField(label=None, widget=HiddenInput()))
    def get_import_data(self):
        return {'type': 'dropbox', 'files': self.files.data}


class BulkTaskTwitterImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='twitter')
    msg_required = lazy_gettext("You must provide some source for the tweets")
    source = TextField(lazy_gettext('Source'),
                       [validators.Required(message=msg_required)])
    max_tweets = IntegerField(lazy_gettext('Number of tweets'))
    user_credentials = TextField(label=None)
    def get_import_data(self):
        return {
            'type': 'twitter',
            'source': self.source.data,
            'max_tweets': self.max_tweets.data,
            'user_credentials': self.user_credentials.data,
        }


class BulkTaskYoutubeImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='youtube')
    msg_required = lazy_gettext("You must provide a valid playlist")
    playlist_url = URLField(lazy_gettext('Playlist'),
                             [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {
          'type': 'youtube',
          'playlist_url': self.playlist_url.data
        }

class BulkTaskS3ImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='s3')
    files = FieldList(TextField(label=None, widget=HiddenInput()))
    msg_required = lazy_gettext("You must provide a valid bucket")
    bucket = TextField(lazy_gettext('Bucket'),
                       [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {
            'type': 's3',
            'files': self.files.data,
            'bucket': self.bucket.data
        }


class GenericBulkTaskImportForm(object):
    """Callable class that will return, when called, the appropriate form
    instance"""
    _forms = { 'csv': BulkTaskCSVImportForm,
              'gdocs': BulkTaskGDImportForm,
              'epicollect': BulkTaskEpiCollectPlusImportForm,
              'flickr': BulkTaskFlickrImportForm,
              'dropbox': BulkTaskDropboxImportForm,
              'twitter': BulkTaskTwitterImportForm,
              's3': BulkTaskS3ImportForm,
              'youtube': BulkTaskYoutubeImportForm,
              'localCSV': BulkTaskLocalCSVImportForm }

    def __call__(self, form_name, *form_args, **form_kwargs):
        if form_name is None:
            return None
        return self._forms[form_name](*form_args, **form_kwargs)


### Forms for account view

class LoginForm(Form):

    """Login Form class for signin into PYBOSSA."""

    email = TextField(lazy_gettext('E-mail'),
                      [validators.Required(
                          message=lazy_gettext("The e-mail is required"))])

    password = PasswordField(lazy_gettext('Password'),
                             [validators.Required(
                                 message=lazy_gettext(
                                     "You must provide a password"))])


class RegisterForm(Form):

    """Register Form Class for creating an account in PYBOSSA."""

    err_msg = lazy_gettext("Full name must be between 3 and %(fullname)s "
                           "characters long", fullname=USER_FULLNAME_MAX_LENGTH)
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=USER_FULLNAME_MAX_LENGTH, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and %(username_length)s "
                           "characters long", username_length=USER_NAME_MAX_LENGTH)
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('User name'),
                         [validators.Length(min=3, max=USER_NAME_MAX_LENGTH, message=err_msg),
                          pb_validator.NotAllowedChars(),
                          pb_validator.Unique(user_repo.get_by, 'name', err_msg_2),
                          pb_validator.ReservedName('account', current_app)])

    err_msg = lazy_gettext("Email must be between 3 and %(email_length)s "
                           "characters long", email_length=EMAIL_MAX_LENGTH)
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email(),
                            pb_validator.UniqueCaseInsensitive(
                                user_repo.search_by_email,
                                'email_addr',
                                err_msg_2)])

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    if enable_strong_password:
        password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                            validators.EqualTo('confirm', err_msg_2),
                            pb_validator.CheckPasswordStrength()])
    else:
        password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                            validators.EqualTo('confirm', err_msg_2)])

    confirm = PasswordField(lazy_gettext('Repeat Password'))
    project_slug = SelectMultipleField(lazy_gettext('Project'), choices=[])


class UpdateProfileForm(Form):

    """Form Class for updating PYBOSSA's user Profile."""

    id = IntegerField(label=None, widget=HiddenInput())

    err_msg = lazy_gettext("Full name must be between 3 and %(fullname)s "
                           "characters long" , fullname=USER_FULLNAME_MAX_LENGTH)
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=USER_FULLNAME_MAX_LENGTH, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and %(username_length)s "
                           "characters long", username_length=USER_NAME_MAX_LENGTH)
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('Username'),
                     [validators.Length(min=3, max=USER_NAME_MAX_LENGTH, message=err_msg),
                      pb_validator.NotAllowedChars(),
                      pb_validator.Unique(user_repo.get_by, 'name', err_msg_2),
                      pb_validator.ReservedName('account', current_app)])

    err_msg = lazy_gettext("Email must be between 3 and %(email_length)s "
                           "characters long", email_length=EMAIL_MAX_LENGTH)
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email(),
                            pb_validator.Unique(user_repo.get_by, 'email_addr', err_msg_2)])
    subscribed = BooleanField(lazy_gettext('Get email notifications'))

    locale = SelectField(lazy_gettext('Language'))
    ckan_api = TextField(lazy_gettext('CKAN API Key'))
    privacy_mode = BooleanField(lazy_gettext('Privacy Mode'))

    def set_locales(self, locales):
        """Fill the locale.choices."""
        choices = []
        for locale in locales:
            choices.append(locale)
        self.locale.choices = choices


class ChangePasswordForm(Form):

    """Form for changing user's password."""

    current_password = PasswordField(lazy_gettext('Current password'))

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat password'))


class ResetPasswordForm(Form):

    """Class for resetting user's password."""

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New Password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat Password'))


class ForgotPasswordForm(Form):

    """Form Class for forgotten password."""

    err_msg = lazy_gettext("Email must be between 3 and %(email_length)s "
                           "characters long", email_length=EMAIL_MAX_LENGTH)
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email()])


class OTPForm(Form):
    otp = TextField(lazy_gettext('One Time Password'),
                    [validators.Required(message=lazy_gettext(
                        'You must provide a valid OTP code'))])


### Forms for admin view

class SearchForm(Form):
    user = TextField(lazy_gettext('User'))


class CategoryForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(project_repo.get_category_by, 'name',
                                          message="Name is already taken.")])
    description = TextField(lazy_gettext('Description'),
                            [validators.Required()])


### Common forms
class AvatarUploadForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    avatar = FileField(lazy_gettext('Avatar'), validators=[FileRequired()])
    x1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    x2 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y2 = IntegerField(label=None, widget=HiddenInput(), default=0)


class BulkUserCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='usercsvimport')
    _allowed_extensions = set(['csv'])
    def _allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in self._allowed_extensions

    def get_import_data(self):
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return {'type': 'usercsvimport', 'csv_filename': None}
            csv_file = request.files['file']
            if csv_file.filename == '':
                flash('No file selected')
                return {'type': 'usercsvimport', 'csv_filename': None}
            if csv_file and self._allowed_file(csv_file.filename):
                filename = secure_filename(csv_file.filename)
                tmpfile = '{0}/{1}'.format(uploader.upload_folder, filename)
                with open(tmpfile, 'w') as fp:
                    fp.write(csv_file.stream.read())
                return {'type': 'usercsvimport', 'csv_filename': tmpfile}
        return {'type': 'usercsvimport', 'csv_filename': None}


class GenericUserImportForm(object):
    """Callable class that will return, when called, the appropriate form
    instance"""
    _forms = {'usercsvimport': BulkUserCSVImportForm}

    def __call__(self, form_name, *form_args, **form_kwargs):
        if form_name is None:
            return None
        return self._forms[form_name](*form_args, **form_kwargs)


class MetadataForm(Form):
    """Form for admins to add metadata for users."""
    languages = SelectMultipleField(lazy_gettext('Language(s)'), choices=util.languages())
    locations = SelectMultipleField(lazy_gettext('Location(s)'), choices=util.countries())
    start_time = TimeField(lazy_gettext('Start Time'),
        [TimeFieldsValidator(["end_time", "timezone"],
        message="Start time, End time, and Timezone must be filled out for submission")])
    end_time = TimeField(lazy_gettext('End Time'),
        [TimeFieldsValidator(["start_time", "timezone"],
        message="Start time, End time, and Timezone must be filled out for submission")])
    timezone = SelectField(lazy_gettext('Timezone'),
        [TimeFieldsValidator(["start_time", "end_time"],
        message="Start time, End time, and Timezone must be filled out for submission")],
        choices=util.timezones())
    user_type = SelectField(lazy_gettext('Type of user'), choices=util.user_types())
    review = TextAreaField(lazy_gettext('Additional comments'))
