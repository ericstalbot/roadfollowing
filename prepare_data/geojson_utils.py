def get_feature(coords, props, ID=None):
    
    coords = [[round(x, 5), round(y, 5)] for x, y in coords]
    
    props['distance'] = round(props['distance'], 0)
    
    ret = {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": coords
      },
      "properties": props
    }
    
    if ID is not None:
        ret['properties']['id'] = ID
    
    return ret      
