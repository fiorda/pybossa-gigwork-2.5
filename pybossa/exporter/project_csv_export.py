# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
# Cache global variables for timeouts
"""
CSV Exporter module for exporting tasks and tasks results out of PyBossa
"""

import tempfile
from pybossa.exporter import Exporter
from pybossa.exporter.csv_export import CsvExporter
from pybossa.core import uploader, project_repo
from pybossa.util import UnicodeWriter
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class ProjectCsvExporter(CsvExporter):

    def _format_csv_row(self, row, ty):
        tmp = row.keys()
        keys = []
        for k in tmp:
            k = "%s__%s" % (ty, k)
            keys.append(k)

        values = []
        _prefix = "%sinfo" % ty
        for k in keys:
            prefix, k = k.split("__", 1)
            if prefix == _prefix:
                if row['info'].get(k) is not None:
                    values.append(row['info'][k])
                else:
                    values.append(None)
            else:
                if row.get(k) is not None:
                    values.append(row[k])
                else:
                    values.append(None)

        return values

    def _handle_row(self, writer, t, ty):
        normal_ty = filter(lambda char: char.isalpha(), ty)
        writer.writerow(self._format_csv_row(t.dictize(), ty=normal_ty))

    def _get_csv(self, out, writer, table, id, rows=None):
        if rows is None:
            return

        for tr in rows:
            self._handle_row(writer, tr, table)
        out.seek(0)
        yield out.read()

    def _format_headers(self, t, ty):
        tmp = t.dictize().keys()
        task_keys = []
        for k in tmp:
            task_keys.append(k)

        return task_keys

    def _respond_csv(self, ty, base_url, info_only=True):
        out = tempfile.TemporaryFile()
        writer = UnicodeWriter(out)
        t = project_repo.get_projects_report(base_url)

        if t is not None:
            headers = self._format_headers(next(iter(t), None), ty)
            writer.writerow(headers)

            return self._get_csv(out, writer, ty, base_url, t)
        else:
            def empty_csv(out):
                yield out.read()
            return empty_csv(out)

    def _make_zip(self, project, ty):
        name = self._project_name_latin_encoded(project)
        csv_task_generator = self._respond_csv(ty, project.base_url)
        if csv_task_generator is not None:
            # TODO: use temp file from csv generation directly
            datafile = tempfile.NamedTemporaryFile()
            try:
                for line in csv_task_generator:
                    datafile.write(str(line))
                datafile.flush()
                csv_task_generator.close()  # delete temp csv file
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    _zip = self._zip_factory(zipped_datafile.name)
                    _zip.write(
                        datafile.name, secure_filename('%s_%s.csv' % (name, ty)))
                    _zip.close()
                    container = "user_%d" % project.owner_id
                    _file = FileStorage(
                        filename=self.download_name(project, ty), stream=zipped_datafile)
                    uploader.upload_file(_file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def download_name(self, project, ty):
        return super(ProjectCsvExporter, self).download_name(project, ty)

    def pregenerate_zip_files(self, project):
        print "%d (csv)" % project.id
