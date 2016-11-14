import requests
import shapely.geometry
from shapely.geometry import LineString, Point
import networkx
from os.path import join, dirname

apikey = open(join(dirname(__file__),'apikey.txt')).read()


def get_bounding_box(lng0, lat0, lng1, lat1):

    delta_x = 0.1 + abs(lng1 - lng0) * .1

    delta_y = 0.1 + abs(lat1 - lat0) * .1

    min_x, max_x = sorted((lng0, lng1))
    min_x -= delta_x
    max_x += delta_x

    min_y, max_y = sorted((lat0, lat1))
    min_y -= delta_y
    max_y += delta_y

    return min_x, min_y, max_x, max_y



def get_features_by_bounding_box(min_x, min_y, max_x, max_y):
    q = '''SELECT *
        FROM   vermont_roads
        WHERE  the_geom
            &&
            ST_MakeEnvelope (
                {min_x}, {min_y},
                {max_x}, {max_y},
                4326)'''

    q = q.format(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

    r = requests.post(

        'https://ericstalbot.cartodb.com/api/v2/sql',
        params={
            'api_key': apikey,
            'q':q,
            'format':'GeoJSON'
            },
    )

    return r.json()


def get_graph(features):


    g = networkx.MultiGraph()

    for fet in features['features']:
        props = fet['properties']
        anode = props['nodea']
        bnode = props['nodeb']
        ID = props['cartodb_id']
        distance = props['distance']
        assert fet['geometry']['type'] == 'MultiLineString'
        coords = fet['geometry']['coordinates'][0]
        shape = shapely.geometry.LineString(coords)


        g.add_edge(anode, bnode, ID,
            shape_orientation = (anode, bnode),
            distance=distance,
            shape=shape)

    return g


def get_nearest_link(g, point):

    def get_distances(g=g, point=point):
        for u, v, k, data in g.edges_iter(keys=True, data=True):
            yield point.distance(data['shape']), u, v, k

    return min(get_distances())[1:]


def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    if distance <= 0.0:
        assert 0
    if distance >= 1:
        assert 0
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p), True)
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance, True)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]

def insert_node(g, x, y):

    point = shapely.geometry.Point(x, y)

    nearest_link = get_nearest_link(g, point)

    u, v, k = nearest_link

    u, v = g[u][v][k]['shape_orientation']

    shape = g[u][v][k]['shape']

    distance_along = shape.project(point, True)

    if distance_along <= 1e-12:
        return u
    if distance_along >= (1-1e-12):
        return v

    snapped_point = shape.interpolate(distance_along, True)

    line_parts = cut(shape, distance_along)

    new_node = networkx.utils.generate_unique_node()

    new_link_id0 = networkx.utils.generate_unique_node()

    new_link_id1 = networkx.utils.generate_unique_node()


    props = g[u][v][k].copy()
    props.update({
        'shape_orientation': (u, new_node),
        'distance': props['distance']*distance_along,
        'shape': line_parts[0]})
    g.add_edge(u, new_node, new_link_id0, **props)

    props = g[u][v][k].copy()
    props.update({
        'shape_orientation': (new_node, v),
        'distance': props['distance']*(1-distance_along),
        'shape': line_parts[1]})
    g.add_edge(new_node, v, new_link_id1, **props)

    g.remove_edge(u, v, k)

    return new_node

def get_shortest_path_links(g, nd0, nd1):

    path = networkx.shortest_path(g, nd0, nd1, weight='distance')

    def get_link_distances(g, a, b):
        for k in g[a][b]:
            yield g[a][b][k]['distance'], k

    for a, b in zip(path[:-1], path[1:]):
        _, k = min(get_link_distances(g, a, b))

        yield a, b, k

def get_path_coords(g, path_links):

    c = []
    for a, b, k in path_links:

        coords = g[a][b][k]['shape'].coords[:]

        if (a, b) != g[a][b][k]['shape_orientation']:
            coords = coords[::-1]

        for xy in coords[:-1]:
            yield xy

    yield coords[-1]


def _get_path(p0, p1):

    #query area between/around points
    bbox = get_bounding_box(*p0, *p1)
    features = get_features_by_bounding_box(*bbox) #this is the geojson
    g = get_graph(features)

    nd0 = insert_node(g, *p0)
    nd1 = insert_node(g, *p1)
    #todo : handle nd0 and nd1 are same node
    path_links = get_shortest_path_links(g, nd0, nd1)

    coords = get_path_coords(g, path_links)

    return {'coords': list(coords)}

def get_path(points):
    assert len(points) > 1

    coords = []

    for p0, p1 in zip(points[:-1], points[1:]):
        r = _get_path(p0, p1)
        coords.extend(r['coords'][:-1])

    coords.append(r['coords'][-1])

    return {'coords': coords}

if __name__ == "__main__":


    #make some test points
    p0 = (-72.476723, 43.788497)
    p1 = (-72.454171, 43.785234)

    path = get_path(p0, p1)

    print(list(path['coords']))
