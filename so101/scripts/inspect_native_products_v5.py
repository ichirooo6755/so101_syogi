import adsk.core
import adsk.fusion
print('supported',app.supportedProductTypes)
for name in app.supportedProductTypes:
    try:
        p=app.activeDocument.products.itemByProductType(name)
        if p:
            print('product',name,p.objectType,'design',bool(adsk.fusion.Design.cast(p)))
    except Exception as e: print('product_error',name,str(e))
print('selection',[(s.entity.objectType,getattr(s.entity,'name','')) for s in ui.activeSelections])
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
