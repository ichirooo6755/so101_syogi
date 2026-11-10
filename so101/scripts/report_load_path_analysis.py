"""Summarize results and render a real FE mesh, with explicit limitations."""
from pathlib import Path
import json
import hashlib
import importlib.metadata

import numpy as np
import meshio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'load_path_analysis'
audit=json.loads((OUT/'geometry_audit.json').read_text())
clearance=json.loads((OUT/'flexure_clearances.json').read_text())
levels={level:json.loads((OUT/f'fea_{level}.json').read_text()) for level in ('coarse','fine','refined')}
assert all(clearance['live_source_matches_analysis_snapshot'].values())

def case(data,name,E=1500.):
    return next(r for r in data['cases'] if r['case']==name and r['printed_E_MPa']==E)

comparisons=[]
for name in ('normal_1N','normal_5N','side_X_0p5N','side_Y_0p5N'):
    c,f,r=[case(levels[level],name) for level in ('coarse','fine','refined')]
    comparisons.append({'case':name,'coarse_max_mm':c['max_displacement_mm'],
        'fine_max_mm':f['max_displacement_mm'],'refined_max_mm':r['max_displacement_mm'],
        'coarse_to_fine_relative_change':abs(f['max_displacement_mm']-c['max_displacement_mm'])/f['max_displacement_mm'],
        'fine_to_refined_relative_change':abs(r['max_displacement_mm']-f['max_displacement_mm'])/r['max_displacement_mm']})

checks=[]
for row in levels['refined']['cases']:
    sensor_u=row['parts']['sensor']['max_displacement_mm']
    carrier_u=row['parts']['carrier']['max_displacement_mm']
    cartridge_u=row['parts']['cartridge']['max_displacement_mm']
    # These are conservative displacement-norm bounds, NOT a nonlinear contact
    # solve and NOT a prediction for a flexible printed base.
    gap_bounds={'base_to_carrier':2.-carrier_u,'base_to_cartridge':2.828427124746-cartridge_u,
        'base_to_flexure':clearance['gaps']['base_to_sensor_flexure_mm']-sensor_u,
        'carrier_to_flexure':clearance['gaps']['carrier_to_sensor_flexure_mm']-sensor_u-carrier_u}
    assert min(gap_bounds.values())>0,gap_bounds
    checks.append({'case':row['case'],'remaining_gap_lower_bounds_mm':gap_bounds})

# Linear superposition also bounds simultaneous normal and dragging loads.
normal=case(levels['refined'],'normal_5N'); side=case(levels['refined'],'side_X_0p5N')
combined_bound=normal['max_displacement_mm']+side['max_displacement_mm']
combined_flexure_gap=clearance['gaps']['carrier_to_sensor_flexure_mm']-sum(
    row['parts'][part]['max_displacement_mm'] for row in (normal,side) for part in ('sensor','carrier'))
assert combined_flexure_gap>0
summary={'verdict':'Screening only: idealized mechanical load path is viable; electrical accuracy is not validated',
    'source_unchanged':audit['source_geometry_preserved'],'live_snapshot_match':clearance['live_source_matches_analysis_snapshot'],
    'mesh_comparisons':comparisons,'gap_checks_rigid_base':checks,
    'combined_5N_Z_plus_0p5N_X_max_displacement_upper_bound_mm':combined_bound,
    'combined_carrier_to_flexure_gap_lower_bound_mm':combined_flexure_gap,
    'force_and_moment_balance_checked':True,'actual_gauge_or_bridge_output_simulated':False,
    'mesh_convergence_certified':False,'force_transfer_efficiency_independently_validated':False,
    'mesh_maximum_displacement_change_below_10_percent':max(c['fine_to_refined_relative_change'] for c in comparisons)<.10,
    'software':{name:importlib.metadata.version(name) for name in ('numpy','scipy','gmsh','scikit-fem','meshio','matplotlib')},
    'snapshot_step_sha256':{label:hashlib.sha256((OUT/(label+'.step')).read_bytes()).hexdigest() for label in ('base','carrier','cartridge','sensor')}}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))

# Extract actual external tetrahedron faces and label the face material.
data=meshio.read(OUT/'refined_normal_5N.vtu')
p=data.points; t=data.cells_dict['tetra']; u=data.point_data['displacement_mm']
material=data.cell_data_dict['part_id']['tetra']
all_faces=np.concatenate([t[:,idx] for idx in ((0,1,2),(0,1,3),(0,2,3),(1,2,3))])
owners=np.tile(np.arange(len(t)),4)
sorted_faces=np.sort(all_faces,axis=1)
_,first,counts=np.unique(sorted_faces,axis=0,return_index=True,return_counts=True)
boundary=first[counts==1]
tri=all_faces[boundary]; face_material=material[owners[boundary]]
norm=np.linalg.norm(u,axis=1)
face_norm=norm[tri].mean(axis=1)
fig=plt.figure(figsize=(14,7.5),layout='constrained',facecolor='#fafbfc')
left=fig.add_subplot(121,projection='3d'); right=fig.add_subplot(122,projection='3d')
colors=['#dc7b31','#477dba','#52a68d']
for mat,label in enumerate(('Approx. aluminium sensor','Printed carrier','Brush cartridge')):
    triangles=tri[face_material==mat]
    left.add_collection3d(Poly3DCollection(p[triangles],facecolors=colors[mat],edgecolors='none',alpha=.97))
    left.plot([],[],[],color=colors[mat],linewidth=5,label=label)
# Show the load axis and its lateral eccentricity with the actual coordinates.
cy=audit['brush_axis_mm'][1]
left.plot([50,50],[cy,cy],[-5,47],color='#243247',linestyle='--',linewidth=1.7)
left.quiver(50,cy,-5,0,0,10,color='#bc2637',linewidth=2.6,arrow_length_ratio=.25)
left.text(51,cy,-2,'5 N +Z',color='#bc2637',fontsize=10)
left.plot([30,50],[cy,cy],[48,48],color='#243247',linewidth=1.5)
left.text(37,cy,50,'20 mm offset',fontsize=10,color='#243247')
left.text(23,30,34,'Fixed block',fontsize=9,color='#243247')
left.set_title('Current mechanical load path\nFixed block clamped; mating faces ideally bonded',fontsize=12,pad=17)
left.legend(loc='lower left',fontsize=8,frameon=False)

scale=100.
deformed=p+scale*u
normmap=Normalize(0,float(norm.max()))
cmap=plt.get_cmap('viridis')
right.add_collection3d(Poly3DCollection(deformed[tri],facecolors=cmap(normmap(face_norm)),edgecolors='none',alpha=1))
right.set_title(f'5 N axial load: displacement x{scale:.0f}\nMax {norm.max():.4f} mm; printed E = 1.5 GPa assumed',fontsize=12,pad=17)
colorbar=fig.colorbar(ScalarMappable(norm=normmap,cmap=cmap),ax=right,shrink=.58,pad=.02)
colorbar.set_label('Actual displacement magnitude [mm]',fontsize=9)
for ax in (left,right):
    ax.set_xlim(22,70); ax.set_ylim(-26,41); ax.set_zlim(-6,54)
    ax.set_box_aspect((48,67,60))
    ax.view_init(elev=22,azim=-58)
    ax.set_xlabel('X [mm]',fontsize=9); ax.set_ylabel('Y [mm]',fontsize=9); ax.set_zlabel('Z [mm]',fontsize=9)
    ax.tick_params(labelsize=8)
fig.suptitle('SO101 calligraphy | conditional linear-elastic FEA',fontsize=16,color='#243247')
fig.text(.5,.008,'Not an electrical calibration. Approximate sensor geometry; rigid base; bonded bolt/glue joints. Hidden old cover excluded.',ha='center',fontsize=9,color='#526075')
fig.savefig(OUT/'load_path_result.png',dpi=180,facecolor=fig.get_facecolor())
plt.close(fig)

meshrows='\n'.join(f"| {label} | {levels[label]['mesh']['tetrahedra']:,} | {levels[label]['DOF']:,} | {levels[label]['mesh']['sensor_size_mm']:.2f} |" for label in levels)
caserows='\n'.join(f"| {row['case']} | {np.linalg.norm(row['sensor_cut_force_N']):.6f} | {row['max_displacement_mm']:.4f} | {row['parts']['sensor']['max_displacement_mm']:.4f} |" for row in levels['refined']['cases'])
convergence='\n'.join(f"| {row['case']} | {row['coarse_max_mm']:.5f} | {row['fine_max_mm']:.5f} | {row['refined_max_mm']:.5f} | {row['fine_to_refined_relative_change']*100:.1f}% |" for row in comparisons)
maxchange=max(c['fine_to_refined_relative_change'] for c in comparisons)*100
report=f'''# SO101 書道：ロードセルへの荷重伝達解析

## 結論

解析時点の表示中の構成では、意図しない固定側への接触はなく、仮定した締結が成立する条件で、筆からロードセルへの機械的な荷重経路は成立しています。
ただし、SC616Cの電気出力や測定精度を再現した解析ではありません。「正確な筆圧が読める」ことまでの合格判定ではありません。
元のFusion設計は変更していません。解析用の独立したSTEPコピーだけを使用しました。

![荷重経路と変形](load_path_result.png)

## 対象と仮定

- スナップショット取得: {audit['captured_utc']}。`geometry_audit.json`に各部品の形状・位置・体積を記録。
- 現在の本体、上面形状が追加されたキャリア、復元したM3ナットポケット、筆カートリッジを対象にしています。
- 非表示の旧別体上面カバーは取り付けない条件です。旧カバーは本体と約{audit['native_interferences'][0]['volume_mm3']:.1f} mm³干渉するため、現状の本体と同時使用できません。
- 弾性解析対象はセンサ、キャリア、カートリッジの3固体です。本体は剛体として扱い、センサ固定端の y >= 23.462946 mm を完全拘束しました。本体の弾性変形はこの解析に含めていません。
- ロードセルモデルは既存の近似形状です。実物の内部寸法、ゲージ位置、接着層、保護樹脂、配線の剛性は未再現です。
- アルミは E=69,000 MPa、ポアソン比0.33を仮定しました。メーカーの材質証明値ではありません。
- 印刷部品は E=1,500 MPaと3,000 MPa、ポアソン比0.35の等方弾性体を仮定しました。PETG/PLAの実際の造形品に対する保証値ではなく、積層方向、空隙、クリープを含みません。
- ボルト締結面とカートリッジのフランジ面は理想的な固着接合です。ボルトの緩み、接触の開閉、滑り、樹脂のへたりは解析しません。
- ホットグルーが筆とスリーブを十分に保持する仮定で、スリーブ内面へ合力とモーメントが一致する分布荷重を与えました。グルーの剥離・抜けは未検証です。
- 横荷重の作用点は筆軸上 z=-40 mmを仮定しました。実際の筆先がさらに遠い場合、横力によるモーメントも増えます。
- 重力、ロボットの加速度、衝撃、温度、疲労は含みません。

## CAD上の隙間・接触経路

表示中の4固体（本体・キャリア・カートリッジ・センサ）の体積干渉は0です。接触は締結用の端部とフランジに限られています。
拡大した測定部保護領域に本体・キャリアは入り込んでいません。

| 箇所 | 最小隙間 |
| --- | ---: |
| 本体とキャリア | 2.000 mm |
| 本体とカートリッジ | 2.828 mm |
| 本体とセンサ中央変形部 | 1.500 mm |
| キャリアとセンサ中央変形部 | 0.500 mm |

上記はCAD公称寸法です。造形誤差やグルーのはみ出し、張った配線で隙間をつながないことが必要です。

## 荷重ケースと結果

以下は印刷部品E=1.5 GPa・最細メッシュでの結果です。反力は内部断面の節点力から回収し、力とモーメントの両方の釣り合いを検査しました。

| 荷重ケース | センサ内部を通る合力 N | 組立の最大変位 mm | センサ最大変位 mm |
| --- | ---: | ---: | ---: |
{caserows}

「入力1 Nに対しセンサ断面に1 N」は、この理想接合・単一路のモデルの静的な釣り合いの結果です。独立した測定誤差・伝達効率の検証と読み替えることはできません。

剛体本体と小変形の仮定下では、5 N軸荷重に0.5 NのX横荷重が同時に作用した場合も、変位ノルムの和から得た上限は{combined_bound:.4f} mmです。
キャリアと中央変形部の相対変位を保守的に差し引いても、最小隙間0.5 mmに対し{combined_flexure_gap:.4f} mm以上残る計算です。
これは接触非線形解析ではなく、接触が発生しないことを変位上限でチェックしたものです。本体の変形・造形誤差を含めた保証ではありません。

## 偏心と横荷重に関する重要な点

筆軸x=50 mm、センサ中心x=30 mmなので、横方向の偏心は20 mmです。
したがって軸方向荷重1 Nで20 Nmm、5 Nで100 Nmmのねじりモーメントがセンサに同時に伝わります。
0.5 Nの横荷重でも中央変形部に応力が発生する結果です。これが実際のブリッジ出力にどれだけ混入するかは、ゲージ配置と補償が不明なので算出していません。

よって現状の結論は「力を伝える機構は成立するが、測定値の正確さは未確定」です。
ロードセルの定格1 kgや、仕様書の四隅誤差の数値だけから、この偏心・筆先高さ・横荷重を含む取り付けで同じ精度が出るとは言えません。

## 数値検証

ソルバーはGmshでメッシュ生成、scikit-femで3次元微小変形線形弾性を組み立て、SciPyの疎行列直接法で求解しています。Fusion標準ソルバーでの解析ではありません。
各ケースで剛体並進のゼロひずみ、剛性行列の対称性、拘束外残差、支持反力、センサ断面の力とモーメントの釣り合いを自動検査しました。
メッシュは全固体が接合された1連結成分で、反転要素はありません。

| メッシュ | 四面体要素数 | 自由度数 | センサ部の指定寸法 mm |
| --- | ---: | ---: | ---: |
{meshrows}

| ケース | 粗メッシュ最大変位 mm | 中メッシュ mm | 細メッシュ mm | 中→細の変化 |
| --- | ---: | ---: | ---: | ---: |
{convergence}

最終2メッシュ間の最大変位の差は最大{maxchange:.1f}%です。10%未満の変化という目安も軸荷重ケースでは未達なので、変位量はスクリーニング用の概算にとどめます。厳密な収束証明ではありません。
部品の降伏・強度の合否は判定していません。ボルト周辺の局所応力は理想固着条件に依存し、特に実際のFDM強度と直接比較できません。

## 実物で必要な確認

1. 筆とグルーを付けた状態で、軸方向の既知荷重を複数点加えて校正します。例: 50/100/200 g相当の荷重を、筆先相当位置から正しい軸方向に加えます。校正時のロボット姿勢も記録します。
2. 同じ軸荷重のまま筆先位置と姿勢を変え、読み値の変化を確認します。横荷重だけを与えた場合の出力も確認します。
3. 荷重を増減してヒステリシスとゼロ復帰を測定し、一定荷重で時間変化も確認します。
4. 移動時は筆・キャリアの重量とロボット加速度も信号に入るため、実際の筆圧とは分けて扱います。
5. 中央変形部の隙間、グルーのはみ出し、配線の張り、M3ねじの底付きと緩みを実物で確認します。

## 再実行

```sh
.analysis-venv/bin/python scripts/load_path_fem.py --level coarse
.analysis-venv/bin/python scripts/load_path_fem.py --level fine
.analysis-venv/bin/python scripts/load_path_fem.py --level refined --only-soft
.analysis-venv/bin/python scripts/report_load_path_analysis.py
```

依存パッケージは`../../scripts/requirements-analysis.txt`、元の形状はこのフォルダのSTEP、結果場はVTU、数値一覧はJSONにあります。

## 仕様と方法の出典

- [ユーザー提供のSC616C仕様PDF](../../SC616C-1kg%20load%20cell.pdf): 1 kg定格、アルミ材、4-M3、外形図。ただしゲージ位置や内部詳細、許容ねじりの指定はありません。
- [メーカーのSC616C資料](https://sensor-con.com/products/SC616C-DATASHEET-R2.pdf)
- [HBK: Load application in load cells](https://www.hbkworld.com/en/knowledge/resource-center/articles/load-application-in-load-cells): 荷重導入と寄生荷重の注意。
- [HBK: Installation of Force Transducers](https://cloud.hbkworld.com/en/knowledge/resource-center/articles/installation-of-force-transducers): 偏心、横力、ねじりの影響。
- [Autodesk: Contacts in Simulation studies](https://help.autodesk.com/cloudhelp/ENU/Fusion-Simulate/files/SIM-CONTACT-TYPES.htm): 固着接合と分離接触の区別。
- [Gmsh manual](https://gmsh.info/doc/texinfo/gmsh.html)、[scikit-fem linear elasticity example](https://github.com/kinnala/scikit-fem/blob/master/docs/examples/ex11.py)
'''
(OUT/'REPORT.md').write_text(report,encoding='utf-8')
print(json.dumps(summary,indent=2))
