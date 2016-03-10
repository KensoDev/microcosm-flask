"""
Pagination support.

"""
from flask import request
from marshmallow import fields, Schema
from microcosm_flask.linking import Link, Links
from microcosm_flask.operations import Operation


# NB: it would be nice to use marshmallow schemas in lieu of `to_dict()` functions here
#
# The main obstacles are:
#
#  - The `Page.to_tuples()` form is needed for query string encoding to ensure consistent
#    ordering of query string arguments (and have reliable tests).
#
#  - The `PaginatedList` would need a different schema for every listed item because
#    marshmallow's nested support is static.


class PageSchema(Schema):
    offset = fields.Integer(missing=0)
    limit = fields.Integer(missing=20)

    @classmethod
    def from_request(cls):
        """
        Load paginagtion information as a dictionary from the request args (e.g. query string).

        """
        return cls().load(request.args).data


class Page(object):
    def __init__(self, offset, limit):
        self.offset = offset
        self.limit = limit

    @classmethod
    def from_query_string(cls, qs):
        """
        Create a page from a query string dictionary.

        This dictionary should probably come from `PageSchema.from_request()`.

        """
        return cls(
            offset=qs["offset"],
            limit=qs["limit"],
        )

    @classmethod
    def from_request(cls):
        """
        Create a page from a request.

        """
        return cls.from_query_string(PageSchema.from_request())

    def next(self):
        return Page(
            offset=self.offset + self.limit,
            limit=self.limit,
        )

    def prev(self):
        return Page(
            offset=self.offset - self.limit,
            limit=self.limit,
        )

    def to_dict(self):
        return dict(self.to_tuples())

    def to_tuples(self):
        """
        Convert to tuples for deterministic order when passed to urlencode.

        """
        return [
            ("offset", self.offset),
            ("limit", self.limit),
        ]


class PaginatedList(object):

    def __init__(self, obj, page, items, count, schema=None):
        self.obj = obj
        self.page = page
        self.items = items
        self.count = count
        self.schema = schema

    def to_dict(self):
        return dict(
            count=self.count,
            items=[
                self.schema.dump(item).data if self.schema else item
                for item in self.items
            ],
            _links=self.links.to_dict(),
            **self.page.to_dict()
        )

    @property
    def operation(self):
        return Operation.Search

    @property
    def links(self):
        links = Links()
        links["self"] = Link.for_(self.operation, self.obj, qs=self.page.to_tuples())
        if self.page.offset + self.page.limit < self.count:
            links["next"] = Link.for_(self.operation, self.obj, qs=self.page.next().to_tuples())
        if self.page.offset > 0:
            links["prev"] = Link.for_(self.operation, self.obj, qs=self.page.prev().to_tuples())
        return links