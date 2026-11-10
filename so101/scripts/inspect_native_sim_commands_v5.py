import adsk.core
import adsk.fusion
import json
print('active_product',app.activeProduct.objectType,app.activeProduct.productType)
print(json.dumps([{'id':c.id,'name':c.name} for c in ui.commandDefinitions if
    any(s in c.name for s in ('拘束','荷重','接触','プリチェック','荷重ケース','スタディ マテリアル','メッシュ設定','モーメント'))],ensure_ascii=False,indent=2))
