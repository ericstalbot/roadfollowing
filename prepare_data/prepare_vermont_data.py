from prepare_link_data import get_processed_data
from vtransroads.vtransroads import get_tags, drop
import fiona.crs

import simplejson
from geojson_utils import get_feature
 
 
 
 
data = get_processed_data(
    'data/TransRoad_RDS/Trans_RDS_line.shp',
    fiona.crs.from_epsg(32618),
    drop,
    get_tags)

features = []
 

def get_features():
    for i, props, coords in data:
        fet = get_feature(coords, props, i)
        yield fet
    
    
with open('vermont_roads.geojson', 'wt') as f:
    
    simplejson.dump(
        {'type': 'FeatureCollection',
         'features': get_features()}, 
        f, separators=(',', ':'),
        iterable_as_array=True)