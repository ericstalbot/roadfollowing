import requests
import shapely.geometry
from shapely.geometry import LineString, Point
import networkx

apikey = open('apikey.txt').read()

'''
for making graph

need to handle splitting and inserting nodes

need to handle case where both points on on same link






'''







#def get_nearest_link(lng, lat):
#
#    x_delta = y_delta = .005
#
#    min_x, max_x = lng-x_delta, lng+x_delta
#    min_y, max_y = lat-y_delta, lat+y_delta
#
#    j = get_features_by_bounding_box(min_x, min_y, max_x, max_y)
#     
#    pnt = shapely.geometry.Point(lng, lat)
#    
#    distances = []
#    
#    for fet in j['features']:
#        ID = fet['properties']['cartodb_id'] ###
#        anode = fet['properties']['anode'] ###
#        bnode = fet['properties']['bnode'] ###
#        geom = shapely.geometry.shape(fet['geometry'])
#        d = geom.distance(pnt)
#        distances.append((d, (anode, bnode, ID))
#        
#    distances.sort()
#    
#    return distances[0][1]
        



        



#def get_path(lng0, lat0, lng1, lat1):
#    
#    g = get_graph(lng0, lat0, lng1, lat1)
#    
#    #here down is tricky part
#    
#    
#    nda0, ndb0, id0 = get_nearest_link(lng0, lat0)
#    nda1, ndb1, id1 = get_nearest_link(lng1, lat1)
#    
#    line0 = shapely.geometry.LineString(g[nda0][ndb0][id0]['coords'])
#    line1 = shapely.geometry.LineString(g[nda1][ndb1][id1]['coords'])
#    
#    
#    
#    pnt0 = shapely.geometry.Point(lng0, lat0)
#    pnt1 = shapely.geometry.Point(lng1, lat1)

    
def get_bounding_box(lng0, lat0, lng1, lat1):    

    delta_x = 0.01 + abs(lng1 - lng0) * .1
    
    delta_y = 0.01 + abs(lat1 - lat0) * .1
    
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
    
    print (u, v, k)
    print(type(shape), shape.is_empty)
    
    distance_along = shape.project(point, True)
    
    print(distance_along)
    
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
    
def get_path(g, nd0, nd1):

    path = networkx.shortest_path(g, nd0, nd1, weight='distance')
    
    def get_link_distances(g, a, b):
        for k in g[a][b]:
            yield g[a][b][k]['distance'], k
    
    
    c = []
    for a, b in zip(path[:-1], path[1:]):
        _, k = min(get_link_distances(g, a, b))
        
        coords = g[a][b][k]['shape'].coords[:]
        
        if (a, b) != g[a][b][k]['shape_orientation']:
            coords = coords[::-1]
        
        c.extend(coords[:-1])
            
    c.append(coords[-1])
    
    return c
        
        
        
    
    
    
    
    
    
    
        
if __name__ == "__main__":
    
    
    #make some test points
    p0 = (-72.476723, 43.788497)
    p1 = (-72.454171, 43.785234)
    
    #query area between/around points
    bbox = get_bounding_box(*p0, *p1)
    features = get_features_by_bounding_box(*bbox) #this is the geojson
    g = get_graph(features)
    
    #if two points on on same link
    #node insertion must work
    
    #if nearest point is at endpoint
    #either node insertion must work (not sure how zero-length line strings work)
    #or must return existing node 
    
    
    
    
    nd0 = insert_node(g, *p0)
    nd1 = insert_node(g, *p1)
    
    coords = get_path(g, nd0, nd1)
    
    with open('test.json', 'wt') as f:
        f.write(str(list(map(list, coords))))
    
'''
End goal: web service for getting xy coords for paths that follow roads

[ ] get x, y coords for path between two points (perfect this)
[ ] put web interface on it - get it up and running live (python anywhere?)
[ ] expand to 3 or more points
[ ] add locked points
[ ] add linear ring (same first and last points)
[ ] documentation, github, blog (all online)


extra
[ ] web interface for getting lines



'''    


