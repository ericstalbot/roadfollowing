import fiona
import fiona.crs
from collections import defaultdict
from itertools import count
from shapely.geometry import LineString

import pyproj

wgs84_proj = pyproj.Proj(fiona.crs.from_epsg(4326))

def drop_z(coords):
    return list(zip(*list(zip(*coords))[:2]))

def transform_coords(coords, source_proj, target_proj):
    
    x, y = list(zip(*coords))
    
    
    x, y = pyproj.transform(
        source_proj,
        target_proj,
        x, y)
        
    return list(zip(x, y))
  
def get_rounded_coords(nd_coords):
    x,y = nd_coords
    return int(round(x)), int(round(y))

def get_labeler():
    c = count()
    def next_label(c=c):
        return next(c)
    return defaultdict(next_label)
    
def snap_coords(coords, node_labeler):
    
    coords = [p[:] for p in coords]
    
    coords[0] = get_rounded_coords(coords[0])
    coords[-1] = get_rounded_coords(coords[-1])
    
    nda = node_labeler[coords[0]]
    ndb = node_labeler[coords[-1]]
    
    return nda, ndb, coords
   
    
def process_geometry(
        rec, source_proj, target_proj, 
        node_labeler):
        
    '''target_crs is for snapping, distance, etc'''
        
    geom = rec['geometry']
    assert geom['type'] == 'LineString'
    
    coords = geom['coordinates']
    coords = drop_z(coords)
    coords = transform_coords(coords, source_proj, target_proj)
    nda, ndb, coords = snap_coords(coords, node_labeler)
    
    distance = LineString(coords).length
    
    coords = transform_coords(coords, target_proj, wgs84_proj)
    
    return nda, ndb, coords, distance       

def process_record(
        rec, source_proj, target_proj,
        node_labeler,
        dropper=None,
        props_processor=None):
    
    if dropper is None:
        dropper = lambda rec: False
    
    if dropper(rec):
        return None
    
    if props_processor is None:
        props_processor = lambda rec: rec['properties']
        
    props = props_processor(rec)
        
    nda, ndb, coords, distance = process_geometry(
        rec, source_proj, target_proj, 
        node_labeler)    
        
    
        
    props.update({
        'distance': distance,
        'nodea': nda,
        'nodeb': ndb})
    
    return coords, props
 

def get_processed_data(data_path, target_crs, 
        dropper=None, props_processor=None):

    with fiona.open(data_path) as c:
        source_crs = c.crs
        
    source_proj = pyproj.Proj(source_crs)
    
    target_proj = pyproj.Proj(target_crs)
    
    node_labeler = get_labeler()
    
    
    with fiona.open(data_path) as c:
        for i, rec in enumerate(c):
            to_yield = process_record(
                rec, source_proj, target_proj, 
                node_labeler,
                dropper, props_processor)
            if to_yield is not None:
                
                coords, props = to_yield
                
                yield i, props, coords 