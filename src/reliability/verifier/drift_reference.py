"""Exact drift membership from the pinned original run; no verdict decoding."""
import hashlib
from reliability.verifier.admission_reference import JSONProjection


def drift_reference_ids(path, expected_sha256):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError('Original drift reference SHA-256 mismatch')
    schema={'calls':{'*':{'patched':True,'run':{'results':{'*':{'test_id':True,'status':True}}}}}}
    projected=JSONProjection(raw.decode()).project(schema)
    result={'base':set(),'patched':set()}
    for call in projected.get('calls',[])[:2]:
        tree='patched' if call['patched'] else 'base'
        result[tree].update(row['test_id'] for row in call['run']['results']
                            if row['status'].lower() in ('passed','failed','error'))
    return {tree:sorted(ids) for tree,ids in result.items()}
