import adsk.core
import adsk.fusion
d=adsk.fusion.Design.cast(app.activeProduct)
c=d.rootComponent.occurrences.itemByName('Brush_Load_Carrier:1').component
marker=d.timeline.count-31
d.timeline.markerPosition=marker
for name in ('Carrier_triangular_rib_-1','Carrier_triangular_rib_1'):
    f=c.features.extrudeFeatures.itemByName(name)
    f.timelineObject.rollTo(True)
    try:
        assert f.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('3 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection,adsk.core.ValueInput.createByString('0 deg'))
    finally:
        d.timeline.markerPosition=marker
    print(name,'repositioned outside the screw-head insertion envelope')
