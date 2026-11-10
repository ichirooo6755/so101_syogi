"""Generate an A4 page of four 4x4 ArUco tags at a known print size."""
from base64 import b64encode
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parents[1]
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
entries = [('0', '9a / top left', 15, 45), ('1', '1a / top right', 115, 45),
           ('3', '9i / bottom left', 15, 145), ('2', '1i / bottom right', 115, 145)]
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
       '<rect width="210" height="297" fill="white"/>',
       '<text x="15" y="17" font-size="5" font-family="sans-serif">SO-101 shogi board markers - print at 100%</text>',
       '<text x="15" y="24" font-size="3.2" font-family="sans-serif">Black square: 26 mm. Keep the arrows pointing the same way.</text>']
for ident, label, x, y in entries:
    marker = cv2.aruco.generateImageMarker(dictionary, int(ident), 520)
    ok, png = cv2.imencode('.png', marker)
    if not ok: raise RuntimeError('Cannot encode marker')
    encoded = b64encode(png.tobytes()).decode('ascii')
    out.extend([f'<rect x="{x}" y="{y}" width="40" height="40" fill="white" stroke="#bbb" stroke-dasharray="1 1" stroke-width=".25"/>',
                f'<image x="{x+7}" y="{y+7}" width="26" height="26" href="data:image/png;base64,{encoded}"/>',
                f'<text x="{x}" y="{y-3}" font-size="4" font-family="sans-serif">ID {ident} : {label}</text>',
                f'<text x="{x+17}" y="{y-8}" font-size="4" font-family="sans-serif">UP</text>'])
out.append('<text x="15" y="240" font-size="3.5" font-family="sans-serif">Place each numbered marker outside the matching grid corner.</text>')
out.append('<text x="15" y="247" font-size="3.5" font-family="sans-serif">The black square corner facing the board must meet the grid corner.</text>')
out.append('</svg>')
(ROOT / 'app' / 'board_markers.svg').write_text('\n'.join(out), encoding='utf-8')
