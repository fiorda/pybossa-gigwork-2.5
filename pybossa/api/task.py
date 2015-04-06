# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
"""
PyBossa api module for exposing domain object Task via an API.

This package adds GET, POST, PUT and DELETE methods for:
    * tasks

"""
from pybossa.model.task import Task
from api_base import APIBase
from pybossa.cache import apps as cached_apps


class TaskAPI(APIBase):

    """Class for domain object Task."""

    __class__ = Task

    def _refresh_cache(self, task):
        cached_apps.clean_project(task.app_id)
