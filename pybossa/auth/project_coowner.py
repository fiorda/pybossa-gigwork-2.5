# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2017 SciFabric LTD.
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

from werkzeug.exceptions import BadRequest


class ProjectCoownerAuth(object):
    _specific_actions = []

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, projectcoowner=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, projectcoowner)

    def _create(self, user, projectcoowner=None):
        return False

    def _read(self, user, projectcoowner=None):
        try:
            if user.admin or user.subadmin:
                return True
            else:
                return False
        except:
            # If the user does not pass an `api_key` parameter, raise an exception
            raise BadRequest('Insufficient privilege to make request')

    def _update(self, user, projectcoowner):
        return False

    def _delete(self, user, projectcoowner):
        return False


