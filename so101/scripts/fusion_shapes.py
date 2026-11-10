"""Small mm-based sketch helpers for the live Fusion bridge."""
import adsk.core
import adsk.fusion

class Shapes:
    def __init__(self, design):
        self.d=design; self.r=design.rootComponent
        self.vi=adsk.core.ValueInput.createByString
        self.NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        self.JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
        self.CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    def component(self,name):
        o=self.r.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=name
        return o,o.component
    def sketch(self,c,name,offset,kind='XY'):
        plane=c.xYConstructionPlane if kind=='XY' else c.xZConstructionPlane
        pi=c.constructionPlanes.createInput(); pi.setByOffset(plane,self.vi(f'{offset:.10f} mm'))
        cp=c.constructionPlanes.add(pi); cp.name=name+'_plane'; cp.isLightBulbOn=False
        sk=c.sketches.add(cp); sk.name=name
        return sk
    def pt(self,sk,xyz):
        return sk.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in xyz)))
    def polygon(self,sk,points):
        for a,b in zip(points,points[1:]+points[:1]):
            line=sk.sketchCurves.sketchLines.addByTwoPoints(self.pt(sk,a),self.pt(sk,b)); line.isFixed=True
    def circle(self,sk,xyz,diam):
        p=self.pt(sk,xyz)
        circle=sk.sketchCurves.sketchCircles.addByCenterRadius(p,self.d.unitsManager.evaluateExpression(diam,'mm')/2)
        circle.centerSketchPoint.isFixed=True
        dim=sk.sketchDimensions.addDiameterDimension(circle,adsk.core.Point3D.create(p.x+.7,p.y+.3,0)); dim.parameter.expression=diam
    def extrude(self,c,sk,depth,op,name,positive=True):
        profiles=adsk.core.ObjectCollection.create()
        for profile in sk.profiles: profiles.add(profile)
        ei=c.features.extrudeFeatures.createInput(profiles,op)
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(self.vi(depth)),
             adsk.fusion.ExtentDirections.PositiveExtentDirection if positive else adsk.fusion.ExtentDirections.NegativeExtentDirection)
        if op!=self.NEW: ei.participantBodies=[c.bRepBodies.item(0)]
        feature=c.features.extrudeFeatures.add(ei); feature.name=name; sk.isVisible=False
        assert int(feature.healthState)==0,(name,feature.errorOrWarningMessage)
        return feature
    def box(self,c,name,x0,x1,y0,y1,z,depth,op=None):
        s=self.sketch(c,name,z)
        self.polygon(s,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)])
        return self.extrude(c,s,depth,self.JOIN if op is None else op,name)
    def cylinder_y(self,c,name,x,z,y0,y1,diam,op=None):
        s=self.sketch(c,name,y0,'XZ'); self.circle(s,(x,y0,z),diam)
        return self.extrude(c,s,f'{y1-y0:.10f} mm',self.JOIN if op is None else op,name)
    def capsule_cut_y(self,c,name,x0,x1,z0,z1,y0,y1):
        s=self.sketch(c,name,y0,'XZ'); radius=(z1-z0)/2; z=(z0+z1)/2
        a=(x0+radius,y0,z0); b=(x1-radius,y0,z0); cc=(x1-radius,y0,z1); dd=(x0+radius,y0,z1)
        curves=s.sketchCurves
        curves.sketchLines.addByTwoPoints(self.pt(s,a),self.pt(s,b)).isFixed=True
        curves.sketchArcs.addByThreePoints(self.pt(s,b),self.pt(s,(x1,y0,z)),self.pt(s,cc)).isFixed=True
        curves.sketchLines.addByTwoPoints(self.pt(s,cc),self.pt(s,dd)).isFixed=True
        curves.sketchArcs.addByThreePoints(self.pt(s,dd),self.pt(s,(x0,y0,z)),self.pt(s,a)).isFixed=True
        return self.extrude(c,s,f'{y1-y0:.10f} mm',self.CUT,name)
