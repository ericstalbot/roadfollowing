'''Data and functions for converting VTrans road attributes
to more human-friendly values.'''

aotclass_mapping = [
    ([7], 'trail'),
    ([4], 'class4'),
    ([3], 'class3'),
    ([2]+list(range(21,30)), 'class2'),
    ([1]+list(range(11,20)), 'class1'),
    (list(range(30, 40)), 'stateroute'),
    (list(range(40,50)), 'usroute'),
    (list(range(51, 60)), 'interstate'),
    ([5,6], 'forestservice')
]

surface_mapping = [
    ([1], 'paved'), 
    ([2,3,5,6,9], 'notpaved')
]

def expand_mapping(mapping):
    result = {}
    for k, v in mapping:
        for k2 in k:
            result[k2] = v
    return result
    
aotclass_mapping = expand_mapping(aotclass_mapping)
surface_mapping = expand_mapping(surface_mapping)

def drop(rec):
    aotclass = rec['properties']['AOTCLASS']
    if aotclass not in aotclass_mapping:
        return True
    else:
        return False

tag_dtypes = {'road_class': str, 'is_paved': str}        
        
def get_tags(rec):
    props = rec['properties']
    aotclass = props['AOTCLASS']
    surface = props['SURFACETYP']
    
    tags = {
        'road_class': aotclass_mapping[aotclass],
        'is_paved': surface_mapping[surface]
    }
    
    return tags