"""Private schematic adapter. All numerical mechanics are explicit toy calculations."""
import argparse, json, math
from atlas_store import Store, digest

def validate(data):
    if data.get('format_version') != 1: raise ValueError('unsupported version')
    parts=data['parts']; ids=[p['id'] for p in parts]
    if len(ids)!=len(set(ids)) or not ids: raise ValueError('duplicate/empty parts')
    by={p['id']:p for p in parts}
    anchors=[p['anchor']['id'] for p in parts]
    if len(anchors)!=len(set(anchors)): raise ValueError('duplicate anchors')
    for p in parts:
        xy=p['anchor']['xy']
        if len(xy)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in xy): raise ValueError('invalid anchor')
        seen=set(); current=p
        while current['parent'] is not None:
            if current['id'] in seen: raise ValueError('cycle')
            seen.add(current['id'])
            if current['parent'] not in by: raise ValueError('dangling parent')
            current=by[current['parent']]
    if sum(p['parent'] is None for p in parts)!=1: raise ValueError('one connected root required')
    pocket_ids=set()
    for pocket in data['pockets']:
        if pocket['id'] in pocket_ids or pocket['part_id'] not in by: raise ValueError('invalid pocket link')
        pocket_ids.add(pocket['id'])
        for field in ('water_volume_m3','gas_volume_m3','gas_pressure_absolute_Pa','ambient_pressure_Pa','compliance_m3_per_Pa','actuator_area_m2'):
            v=pocket[field]
            if v is not None and (type(v) not in (int,float) or not math.isfinite(v) or v<0): raise ValueError('invalid physical value')
        v=pocket['water_pressure_gauge_Pa']
        if v is not None and (type(v) not in (int,float) or not math.isfinite(v)): raise ValueError('invalid gauge pressure')
    for v in data['energy'].values():
        if v is not None and (type(v) not in (int,float) or not math.isfinite(v)): raise ValueError('invalid energy')
    return data

def pressure_work_J(pressure_gauge_Pa, delta_volume_m3):
    """Constant gauge-pressure approximation: positive expansion outputs work."""
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in (pressure_gauge_Pa,delta_volume_m3)): raise ValueError('finite values required')
    return pressure_gauge_Pa*delta_volume_m3

def balance_residual_J(energy):
    fields=('input_J','mechanical_output_J','heat_loss_J','stored_change_J')
    if any(energy.get(k) is None for k in fields): return None
    return energy['input_J']-energy['mechanical_output_J']-energy['heat_loss_J']-energy['stored_change_J']

def commit(data,path):
    validate(data)
    # One full scaffold per immutable record: validation precedes any database mutation.
    store=Store(path)
    try:
        return store.append('aurelia-scaffold-'+digest(data),'aurelia.cage.scaffold',data,
          {'locator':'adapter scaffold import; source member '+data['source']['member_sha256'],'evidence':'hypothesis'},expected_head=store.verify())
    finally: store.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('file');parser.add_argument('--db');args=parser.parse_args()
    data=json.load(open(args.file,encoding='utf-8'));validate(data)
    print(json.dumps({'valid':True,'parts':len(data['parts']),'pockets':len(data['pockets']),'energy_residual_J':balance_residual_J(data['energy']),'anchor':commit(data,args.db) if args.db else None},indent=2))
