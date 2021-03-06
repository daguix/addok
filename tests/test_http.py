from addok.http import View


def test_search_without_query_should_return_400(client):
    resp = client.get('/search/')
    assert resp.status_code == 400


def test_search_should_return_geojson(client, factory):
    factory(name='rue des avions')
    resp = client.get('/search/', query_string={'q': 'avions'})
    assert resp.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert resp.json['type'] == 'FeatureCollection'
    assert len(resp.json['features']) == 1
    feature = resp.json['features'][0]
    assert feature['properties']['name'] == 'rue des avions'
    assert feature['properties']['id']
    assert feature['properties']['type']
    assert feature['properties']['score']
    assert 'attribution' in resp.json
    assert 'licence' in resp.json


def test_search_should_have_cors_headers(client, factory):
    factory(name='rue des avions')
    resp = client.get('/search/', query_string={'q': 'avions'})
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    assert resp.headers['Access-Control-Allow-Headers'] == 'X-Requested-With'


def test_search_without_trailing_slash_should_not_be_redirected(client):
    resp = client.get('/search', query_string={'q': 'avions'})
    assert resp.status_code == 200


def test_search_can_be_filtered(client, factory):
    factory(name='rue de Paris', type="street")
    factory(name='Paris', type="city")
    resp = client.get('/search/', query_string={'q': 'paris', 'type': 'city'})
    assert resp.json['type'] == 'FeatureCollection'
    assert len(resp.json['features']) == 1
    feature = resp.json['features'][0]
    assert feature['properties']['name'] == 'Paris'
    assert feature['properties']['type'] == 'city'


def test_search_filters_can_be_combined(client, factory):
    factory(name='rue de Paris', type="street", postcode="77000")
    factory(name='avenue de Paris', type="street", postcode="22000")
    factory(name='Paris', type="city")
    resp = client.get('/search/', query_string={'q': 'paris', 'type': 'street',
                                                'postcode': '77000'})
    assert resp.json['type'] == 'FeatureCollection'
    assert len(resp.json['features']) == 1
    feature = resp.json['features'][0]
    assert feature['properties']['name'] == 'rue de Paris'
    assert feature['properties']['type'] == 'street'


def test_reverse_should_return_geojson(client, factory):
    factory(name='rue des avions', lat=44, lon=4)
    resp = client.get('/reverse/', query_string={'lat': '44', 'lon': '4'})
    assert resp.json['type'] == 'FeatureCollection'
    assert len(resp.json['features']) == 1
    feature = resp.json['features'][0]
    assert feature['properties']['name'] == 'rue des avions'
    assert feature['properties']['id']
    assert feature['properties']['type']
    assert feature['properties']['score']
    assert 'attribution' in resp.json
    assert 'licence' in resp.json


def test_reverse_should_also_accept_lng(client, factory):
    factory(name='rue des avions', lat=44, lon=4)
    resp = client.get('/reverse/', query_string={'lat': '44', 'lng': '4'})
    assert len(resp.json['features']) == 1


def test_reverse_without_trailing_slash_should_not_be_redirected(client):
    resp = client.get('/reverse', query_string={'lat': '44', 'lon': '4'})
    assert resp.status_code == 200


def test_reverse_can_be_filtered(client, factory):
    factory(lat=48.234545, lon=5.235445, type="street")
    factory(lat=48.234546, lon=5.235446, type="city")
    resp = client.get('/reverse/', query_string={'lat': '48.234545',
                                                 'lon': '5.235446',
                                                 'type': 'city'})
    assert resp.json['type'] == 'FeatureCollection'
    assert len(resp.json['features']) == 1
    feature = resp.json['features'][0]
    assert feature['properties']['type'] == 'city'


def test_reverse_should_have_cors_headers(client, factory):
    factory(name='rue des avions', lat=44, lon=4)
    resp = client.get('/reverse/', query_string={'lat': '44', 'lng': '4'})
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    assert resp.headers['Access-Control-Allow-Headers'] == 'X-Requested-With'


def test_get_endpoint(client, factory):
    factory(name='sentier de la côte', id='123')
    resp = client.get('/get/123')
    assert resp.json['properties']['id'] == '123'


def test_get_endpoint_with_invalid_id(client):
    resp = client.get('/get/123')
    assert resp.status_code == 404


def test_get_should_have_cors_headers(client, factory):
    factory(name='sentier de la côte', id='123')
    resp = client.get('/get/123')
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    assert resp.headers['Access-Control-Allow-Headers'] == 'X-Requested-With'


def test_view_should_expose_config(config):
    config.NEW_PROPERTY = "ok"
    assert View.config.NEW_PROPERTY == "ok"


def test_geojson_should_return_housenumber_payload(client, factory, config):
    config.HOUSENUMBERS_PAYLOAD_FIELDS = ['key']
    factory(name="rue de Paris", type="street", id="123",
            housenumbers={'1': {'lat': '48.32', 'lon': '2.25', 'key': 'abc'}})
    resp = client.get('/search/', query_string={'q': 'rue de paris'})
    assert 'key' not in resp.json['features'][0]['properties']
    resp = client.get('/search/', query_string={'q': '1 rue de paris'})
    assert resp.json['features'][0]['properties']['key'] == 'abc'


def test_geojson_should_keep_housenumber_parent_name(client, factory):
    factory(name="rue de Paris", type="street", id="123",
            housenumbers={'1': {'lat': '48.32', 'lon': '2.25'}})
    factory(name="Le Vieux-Chêne", type="locality", id="124",
            housenumbers={'2': {'lat': '48.22', 'lon': '2.22'}})
    resp = client.get('/search/', query_string={'q': '1 rue de paris'})
    assert resp.json['features'][0]['properties']['name'] == '1 rue de Paris'
    assert resp.json['features'][0]['properties']['street'] == 'rue de Paris'
    resp = client.get('/search/', query_string={'q': '2 Le Vieux-Chêne'})
    assert resp.json['features'][0]['properties']['name'] == '2 Le Vieux-Chêne'
    assert resp.json['features'][0]['properties']['locality'] == 'Le Vieux-Chêne'
