# Django 5 / python 3 compatibility (c) 2025, Ivor Bosloper <ivorbosloper@gmail.com>
# All rights reserved.
#
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
from hashlib import md5
from mimetypes import guess_type
from urllib.parse import quote as urlquote

from djangodav.utils import rfc1123_date, rfc3339_date, safe_join


class BaseDavResource:
    ALL_PROPS = [
        "getcontentlength",
        "creationdate",
        "getlastmodified",
        "resourcetype",
        "displayname",
    ]

    LIVE_PROPERTIES = [
        "{DAV:}getetag",
        "{DAV:}getcontentlength",
        "{DAV:}creationdate",
        "{DAV:}getlastmodified",
        "{DAV:}resourcetype",
        "{DAV:}displayname",
    ]

    def __init__(self, path=None, user=None):
        self.path = []
        path = path.strip("/")
        if path:
            self.path = path.split("/")
        self.user = user

    def get_path(self):
        return self.construct_path(self.path, self.is_collection)

    def get_escaped_path(self):
        path = [urlquote(p) for p in self.path]
        return self.construct_path(path, self.is_collection)

    def construct_path(self, path, is_collection):
        return ("/" if path else "") + "/".join(path) + ("/" * (is_collection))

    @property
    def displayname(self):
        if len(self.path) == 0:
            return "/"
        if not self.path:
            return None
        return self.path[-1]

    @property
    def is_root(self):
        return not bool(self.path)

    def get_parent_path(self):
        path = self.path[:-1]
        return "/" + "/".join(path) + "/" if path else ""

    def get_parent(self):
        return self.clone(self.get_parent_path())

    def get_descendants(self, depth=1, include_self=True):
        """Return an iterator of all descendants of this resource."""
        if include_self:
            yield self
        # If depth is less than 0, then it started out as -1.
        # We need to keep recursing until we hit 0, or forever
        # in case of infinity.
        if depth != 0:
            for child in self.get_children():
                for desc in child.get_descendants(depth=depth - 1, include_self=True):
                    yield desc

    @property
    def getcontentlength(self):
        # The property name is "getcontentlength". A get- property is unpythonic, but is exactly aligned with the spec
        # https://www.rfc-editor.org/rfc/rfc4918#section-15.4
        raise NotImplementedError()

    @property
    def creationdate(self):
        """Return the create time as rfc3339_date."""
        return rfc3339_date(self.get_created())

    @property
    def getlastmodified(self):
        """Return the modified time as http_date."""
        # The property name is "getlastmodified". A get- property is unpythonic, but is exactly aligned with the spec
        # https://www.rfc-editor.org/rfc/rfc4918#section-15.7
        return rfc1123_date(self.get_modified())

    def get_created(self):
        """Return the create time as datetime object."""
        raise NotImplementedError()

    def get_modified(self):
        """Return the modified time as datetime object."""
        raise NotImplementedError()

    @property
    def getetag(self):
        # The property name is "getetag". A get- property is unpythonic, but is exactly aligned with the spec
        # https://www.rfc-editor.org/rfc/rfc4918#section-15.6
        raise NotImplementedError()

    def copy(self, destination, depth=-1):
        if self.is_collection:
            if not destination.exists or not destination.is_collection:
                destination.create_collection()
            self.copy_collection(destination, depth)
        else:
            if destination.is_object:
                destination.delete()
            self.copy_object(destination)

    def copy_collection(self, destination, depth=-1):
        """Called to copy a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to copy to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type. It also needs to respect the depth
        parameter. depth == -1 is infinity."""
        # If depth is less than 0, then it started out as -1.
        # We need to keep recursing until we hit 0, or forever
        # in case of infinity.
        if depth != 0 and self.is_collection:
            for child in self.get_children():
                child.copy(
                    self.clone(safe_join(destination.get_path(), child.displayname)),
                    depth=depth - 1,
                )

    def copy_object(self, destination):
        raise NotImplementedError()

    def move(self, destination):
        if self.is_collection:
            if not destination.exists or not destination.is_collection:
                destination.create_collection()
            self.move_collection(destination)
        else:
            if destination.is_object:
                destination.delete()
            self.move_object(destination)

    def move_collection(self, destination):
        """Called to move a resource to a new location. Overwrite is assumed, the DAV server
        will refuse to move to an existing resource otherwise. This method needs to gracefully
        handle a pre-existing destination of any type."""
        for child in self.get_children():
            child.move(self.clone(safe_join(destination.get_path(), child.displayname)))
        self.delete()

    def clone(self, *args, **kwargs):
        clone = self.__class__(*args, **kwargs)
        clone.user = self.user
        return clone

    def move_object(self, destination):
        raise NotImplementedError()

    def write(self, request, temp_file=None, range_start=None):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    @property
    def is_collection(self):
        raise NotImplementedError()

    @property
    def content_type(self):
        return guess_type(self.displayname)[0]

    @property
    def is_object(self):
        raise NotImplementedError()

    @property
    def exists(self):
        raise NotImplementedError()

    def get_children(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def create_collection(self):
        raise NotImplementedError()


class MetaEtagMixIn:
    @property
    def getetag(self):
        """Calculate an etag for this resource. The default implementation uses an md5 sub of the
        absolute path modified time and size. Can be overridden if resources are not stored in a
        file system. The etag is used to detect changes to a resource between HTTP calls. So this
        needs to change if a resource is modified."""
        hashsum = md5()
        hashsum.update(self.displayname.encode())
        hashsum.update(str(self.creationdate).encode())
        hashsum.update(str(self.getlastmodified).encode())
        hashsum.update(str(self.getcontentlength).encode())
        return hashsum.hexdigest()
