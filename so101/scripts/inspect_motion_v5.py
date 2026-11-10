import adsk.core
import adsk.fusion
import json
import os

d = adsk.fusion.Design.cast(app.activeProduct)
assert d and app.activeDocument.name == 'so101書道'
r = d.rootComponent
root = '/Users/sugawaraichirou/Documents/ChatGPT/so101'
dest = root + '/tmp/v5_before.json'
assert not os.path.exists(dest), 'Preserve the first v5 snapshot'
def point(p):
    return [v * 10 for v in p.asArray()]
def safe(obj, names):
    result = {}
    for name in names:
        try:
            value = getattr(obj, name)
            if hasattr(value, 'asArray'):
                value = list(value.asArray())
            elif hasattr(value, 'objectType'):
                value = {'type': value.objectType, 'name': getattr(value, 'name', '')}
            elif not isinstance(value, (str, bool, int, float, type(None))):
                value = str(value)
            result[name] = value
        except Exception as ex:
            result[name] = str(ex)
    return result
data = {'document': app.activeDocument.name, 'modified': app.activeDocument.isModified,
        'timeline_marker': d.timeline.markerPosition, 'timeline_count': d.timeline.count,
        'parameters': {p.name: p.expression for p in d.userParameters},
        'occurrences': [], 'joints': [], 'as_built_joints': [],
        'workspaces': [{'id': w.id, 'name': w.name, 'active': w.isActive} for w in ui.workspaces],
        'sim_commands': [{'id': c.id, 'name': c.name} for c in ui.commandDefinitions
                         if any(t in (c.id + ' ' + c.name).lower() for t in ('simulat', 'stress', 'mesh', 'solve', 'study'))]}
for o in r.allOccurrences:
    data['occurrences'].append({'name': o.fullPathName, 'visible': o.isVisible, 'light': o.isLightBulbOn,
        'transform': list(o.transform2.asArray()), 'grounded': o.isGrounded,
        'bodies': [{'name': b.name, 'volume_mm3': b.volume * 1000,
                    'bbox_mm': [point(b.boundingBox.minPoint), point(b.boundingBox.maxPoint)]}
                   for b in o.bRepBodies]})
for collection, name in ((r.joints, 'joints'), (r.asBuiltJoints, 'as_built_joints')):
    for j in collection:
        entry = safe(j, ('name', 'isSuppressed', 'occurrenceOne', 'occurrenceTwo', 'isLocked',
                         'geometryOrOriginOne', 'geometryOrOriginTwo', 'geometry', 'angle', 'offset',
                         'isFlipped', 'healthState', 'errorOrWarningMessage'))
        try:
            jm = j.jointMotion
            entry['motion'] = safe(jm, ('jointType', 'rotationAxis', 'rotationAxisVector', 'rotationValue',
                                      'slideDirectionVector', 'rotationLimits'))
            if hasattr(jm, 'rotationLimits'):
                entry['rotation_limits'] = safe(jm.rotationLimits, ('isMinimumValueEnabled', 'minimumValue',
                                                                   'isMaximumValueEnabled', 'maximumValue'))
        except Exception as ex:
            entry['motion_error'] = str(ex)
        data[name].append(entry)
archive = root + '/reference/so101_before_motion_redesign_v5.f3d'
assert not os.path.exists(archive)
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(archive))
with open(dest, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(json.dumps({'document': data['document'], 'modified': data['modified'],
                  'timeline': [data['timeline_marker'], data['timeline_count']],
                  'visible': [o for o in data['occurrences'] if o['visible']],
                  'joints': data['joints'], 'as_built_joints': data['as_built_joints'],
                  'workspaces': data['workspaces'], 'sim_commands': data['sim_commands']},
                 ensure_ascii=False, indent=2))
