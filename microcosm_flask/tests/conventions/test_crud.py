"""
CRUD convention tests.

"""
from json import dumps, loads

from hamcrest import (
    assert_that,
    contains_inanyorder,
    equal_to,
    is_,
)

from microcosm.api import create_object_graph
from microcosm_flask.conventions.crud import configure_crud
from microcosm_flask.operations import Operation
from microcosm_flask.paging import PageSchema
from microcosm_flask.tests.conventions.fixtures import (
    NewPersonSchema,
    person_create,
    person_delete,
    person_replace,
    person_retrieve,
    person_search,
    person_update,
    Person,
    PersonSchema,
    PERSON_ID_1,
    PERSON_ID_2,
)


PERSON_MAPPINGS = {
    Operation.Create: (person_create, NewPersonSchema(), PersonSchema()),
    Operation.Delete: (person_delete,),
    Operation.Replace: (person_replace, NewPersonSchema(), PersonSchema()),
    Operation.Retrieve: (person_retrieve, PersonSchema()),
    Operation.Search: (person_search, PageSchema(), PersonSchema()),
    Operation.Update: (person_update, NewPersonSchema(), PersonSchema()),
}


class TestCrud(object):

    def setup(self):
        self.graph = create_object_graph(name="example", testing=True)
        configure_crud(self.graph, Person, PERSON_MAPPINGS)
        self.client = self.graph.flask.test_client()

    def assert_response(self, response, status_code, data=None):
        # always validate status code
        assert_that(response.status_code, is_(equal_to(status_code)))

        # expect JSON data except on 204
        if status_code == 204:
            response_data = None
        else:
            response_data = loads(response.get_data())

        # validate data if provided
        if response_data is not None and data is not None:
            assert_that(response_data, is_(equal_to(data)))

    def test_search(self):
        uri = "/api/person"
        response = self.client.get(uri)
        self.assert_response(response, 200, {
            "count": 1,
            "offset": 0,
            "limit": 20,
            "items": [{
                "id": str(PERSON_ID_1),
                "firstName": "Alice",
                "lastName": "Smith",
                "_links": {
                    "self": {
                        "href": "http://localhost/api/person/{}".format(PERSON_ID_1),
                    }
                },
            }],
            "_links": {
                "self": {
                    "href": "http://localhost/api/person?offset=0&limit=20",
                }
            }
        })

    def test_create(self):
        request_data = {
            "firstName": "Bob",
            "lastName": "Jones",
        }
        response = self.client.post("/api/person", data=dumps(request_data))
        self.assert_response(response, 201, {
            "id": str(PERSON_ID_2),
            "firstName": "Bob",
            "lastName": "Jones",
            "_links": {
                "self": {
                    "href": "http://localhost/api/person/{}".format(PERSON_ID_2),
                }
            },
        })

    def test_create_empty_object(self):
        response = self.client.post("/api/person", data='{}')
        self.assert_response(response, 422)
        response_data = loads(response.get_data())
        assert_that(response_data["context"]["errors"], contains_inanyorder(
            {
                "message": "Could not validate field: lastName",
                "field": "lastName",
                "reasons": [
                    "Missing data for required field.",
                ],
            }, {
                "message": "Could not validate field: firstName",
                "field": "firstName",
                "reasons": [
                    "Missing data for required field.",
                ],
            }
        ))

    def test_create_malformed(self):
        request_data = {
            "lastName": "Jones",
        }
        response = self.client.post("/api/person", data=dumps(request_data))
        self.assert_response(response, 422, {
            "code": 422,
            "message": "Validation error",
            "retryable": False,
            "context": {
                "errors": [{
                    "message": "Could not validate field: firstName",
                    "field": "firstName",
                    "reasons": [
                        "Missing data for required field.",
                    ],
                }]
            }
        })

    def test_retrieve(self):
        uri = "/api/person/{}".format(PERSON_ID_1)
        response = self.client.get(uri)
        self.assert_response(response, 200, {
            "id": str(PERSON_ID_1),
            "firstName": "Alice",
            "lastName": "Smith",
            "_links": {
                "self": {
                    "href": "http://localhost/api/person/{}".format(PERSON_ID_1),
                }
            },
        })

    def test_retrieve_not_found(self):
        uri = "/api/person/{}".format(PERSON_ID_2)
        response = self.client.get(uri)
        self.assert_response(response, 404)

    def test_delete(self):
        uri = "/api/person/{}".format(PERSON_ID_1)
        response = self.client.delete(uri)
        self.assert_response(response, 204)

    def test_delete_not_found(self):
        uri = "/api/person/{}".format(PERSON_ID_2)
        response = self.client.delete(uri)
        self.assert_response(response, 404)

    def test_replace(self):
        uri = "/api/person/{}".format(PERSON_ID_1)
        request_data = {
            "firstName": "Bob",
            "lastName": "Jones",
        }
        response = self.client.put(uri, data=dumps(request_data))
        self.assert_response(response, 200, {
            "id": str(PERSON_ID_1),
            "firstName": "Bob",
            "lastName": "Jones",
            "_links": {
                "self": {
                    "href": "http://localhost/api/person/{}".format(PERSON_ID_1),
                }
            },
        })

    def test_update(self):
        uri = "/api/person/{}".format(PERSON_ID_1)
        request_data = {
            "firstName": "Bob",
        }
        response = self.client.patch(uri, data=dumps(request_data))
        self.assert_response(response, 200, {
            "id": str(PERSON_ID_1),
            "firstName": "Bob",
            "lastName": "Smith",
            "_links": {
                "self": {
                    "href": "http://localhost/api/person/{}".format(PERSON_ID_1),
                }
            },
        })

    def test_update_not_found(self):
        uri = "/api/person/{}".format(PERSON_ID_2)
        request_data = {
            "firstName": "Bob",
        }
        response = self.client.patch(uri, data=dumps(request_data))
        self.assert_response(response, 404)
