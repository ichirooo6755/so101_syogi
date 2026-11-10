import adsk.core
import adsk.fusion
d=adsk.fusion.Design.cast(app.activeProduct)
c=d.rootComponent.occurrences.itemByName('Brush_Cartridge_15mm:1').component
vi=adsk.core.ValueInput.createByString
if not d.userParameters.itemByName('brush_guide_dia'):
    d.userParameters.add('brush_guide_dia',vi('brush_dia + 0.4 mm'),'mm','Slip guide at both sleeve ends; no clamp or interference fit')
y=d.userParameters.itemByName('sc_brush_axis_y').value
for index,z in enumerate((-5.5,28.5)):
    inp=c.constructionPlanes.createInput(); inp.setByOffset(c.xYConstructionPlane,vi(f'{z} mm'))
    pl=c.constructionPlanes.add(inp); pl.name='Brush_centering_land_'+str(index); pl.isLightBulbOn=False
    for op,diam,label in ((adsk.fusion.FeatureOperations.JoinFeatureOperation,'brush_cartridge_od','fill'),
                          (adsk.fusion.FeatureOperations.CutFeatureOperation,'brush_guide_dia','slip_guide')):
        sk=c.sketches.add(pl); sk.name='Brush_centering_'+label+'_'+str(index)
        center=adsk.core.Point3D.create(5,y,0)
        circle=sk.sketchCurves.sketchCircles.addByCenterRadius(center,d.userParameters.itemByName(diam).value/2)
        circle.centerSketchPoint.isFixed=True
        dim=sk.sketchDimensions.addDiameterDimension(circle,adsk.core.Point3D.create(6,y+0.4,0)); dim.parameter.expression=diam
        ei=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi('2 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        ei.participantBodies=[c.bRepBodies.item(0)]
        f=c.features.extrudeFeatures.add(ei); f.name='Brush_centering_'+label+'_'+str(index); sk.isVisible=False
        assert int(f.healthState)==0
print('Added two 2 mm centering lands: brush_dia + 0.4 mm, middle bore brush_dia + 1 mm')
