# Refactoring, Django 1.11 compatibility, cleanups, bugfixes (c) 2018 Christian Kreuzberger <ckreuzberger@anexia-it.com>
# All rights reserved.
#
# Portions (c) 2014, Alexander Klimenko <alex@erix.ru>
# All rights reserved.
#
# Copyright (c) 2011, SmartFile <btimby@smartfile.com>
# All rights reserved.
#
# This file is part of DjangoDav.
#
# DjangoDav is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DjangoDav is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with DjangoDav.  If not, see <http://www.gnu.org/licenses/>.
from datetime import datetime, timezone

from mock import MagicMock, Mock

from djangodav.base.resources import BaseDavResource


class MockResource(MagicMock, BaseDavResource):
    exists = True
    get_created = Mock(return_value=datetime(1983, 12, 24, 6, tzinfo=timezone.utc))
    get_modified = Mock(return_value=datetime(2014, 12, 24, 6, tzinfo=timezone.utc))
    getcontentlength = 0

    def __init__(self, path, *args, **kwargs):
        super(MockResource, self).__init__(spec=BaseDavResource, *args, **kwargs)
        BaseDavResource.__init__(self, path)


class MockObject(MockResource):
    getetag = "0" * 40
    is_object = True
    is_collection = False
    getcontentlength = 42


class MockCollection(MockResource):
    is_object = False
    is_collection = True


class MissingMockResource(MockResource):
    exists = False


class MissingMockObject(MissingMockResource):
    is_object = True
    is_collection = False
    getcontentlength = 42


class MissingMockCollection(MissingMockResource):
    is_object = False
    is_collection = True
