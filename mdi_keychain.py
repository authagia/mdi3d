import os
import subprocess
import shutil
from svgelements import SVG, Path, Move, Line, Polyline, Polygon, Circle, Ellipse, Rect
import numpy as np
from svg_sampling import extract_points, create_base_svg

# === 設定パラメータ ===
INPUT_SVG = "./mdi_svg/skate-off.svg"        # 処理したい元のSVGファイル名
OUTPUT_DIR = "./stl"        # 出力先のディレクトリ
TARGET_SIZE_MM = 60.0         # 6cm四方にスケーリング
BASE_THICKNESS_MM = 3.0       # 土台（ベース）の厚み
DESIGN_THICKNESS_MM = 1.5     # デザイン部（浮き彫り）の厚み
OFFSET_MM = 3.0               # フチの余白（オフセット幅）

EYELET_HOLE_RAD = 2.5         # アイレットの穴の半径（直径5mm）
EYELET_OUTER_RAD = 5.0        # アイレットの外径の半径（直径10mm）

# OpenSCADの実行パス (環境に合わせて変更してください)
# Windowsの一般的なパス: "C:\\Program Files\\OpenSCAD\\openscad.exe"
# Macの一般的なパス: "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
OPENSCAD_PATH = "./OpenSCAD-2021.01-x86-64/openscad-2021.01/openscad.com" 

def extract_points_from_svg(svg_path, target_size):
    """Wrapper that calls svg_sampling.extract_points with sensible defaults."""
    pts, scale, bbox = extract_points(svg_path, target_size, sampling_mode='recursive', params={'tol_mm':0.25, 'max_depth':12})
    return pts, scale, bbox

def create_base_svg_wrapper(points, offset, output_path):
    """Wrapper that calls svg_sampling.create_base_svg with defaults (round joins)."""
    return create_base_svg(points, offset, output_path, join_style='round')

def main():
    if not os.path.exists(INPUT_SVG):
        print(f"エラー: 入力ファイル '{INPUT_SVG}' が見つかりません。")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    design_svg_path = os.path.join(OUTPUT_DIR, "design.svg")
    base_svg_path = os.path.join(OUTPUT_DIR, "base.svg")
    scad_path = os.path.join(OUTPUT_DIR, "model.scad")
    stl_path = os.path.join(OUTPUT_DIR, "keychain.stl")
    
    print("1. SVGの解析とスケーリング中...")
    points, scale_factor, bbox = extract_points_from_svg(INPUT_SVG, TARGET_SIZE_MM)
    
    # OpenSCAD側でサイズを合わせるため、元デザインもスケール変換をかけた状態で複製保存
    # ※元のサイズから一元管理するため、svgelementsでスケール変換を適用して保存
    input_svg_obj = SVG.parse(INPUT_SVG)
    input_svg_obj.transform = f"scale({scale_factor}) translate({-bbox[0]}, {-bbox[3]})"
    # OpenSCADのインポート互換性のため、Y軸方向の反転を考慮
    with open(design_svg_path, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TARGET_SIZE_MM*2} {TARGET_SIZE_MM*2}" width="{TARGET_SIZE_MM*2}mm" height="{TARGET_SIZE_MM*2}mm">\n')
        f.write(f'  <g transform="scale(1, -1) translate(0, {-TARGET_SIZE_MM})">\n')
        with open(INPUT_SVG, 'r') as orig:
            f.write(orig.read())
        f.write('  </g>\n</svg>\n')
    
    # 実際はより安全に、元のデザインをそのまま引き渡せるようOpenSCAD側でスケールさせます
    shutil.copyfile(INPUT_SVG, design_svg_path)

    print("2. 凸包の計算とベース（土台）の生成中...")
    offset_poly = create_base_svg_wrapper(points, OFFSET_MM, base_svg_path)
    
    # アイレット（穴）を配置するための、ベースの最上部座標と重心を取得
    centroid = offset_poly.centroid
    cx, cy = centroid.x, centroid.y
    
    # 一番上のY座標を持つ点を探索
    exterior_coords = list(offset_poly.exterior.coords)
    top_point = max(exterior_coords, key=lambda p: p[1])
    top_x, top_y = top_point[0], top_point[1]

    print("3. OpenSCADスクリプト(.scad)の作成中...")
    # OpenSCADコードの組み立て
    scad_code = f"""// 自動生成されたキーホルダーモデル
$fn = 60; // 円の分割数（滑らかさ）

// パラメータ
base_h = {BASE_THICKNESS_MM};
design_h = {DESIGN_THICKNESS_MM};
scale_f = {scale_factor};
orig_x1 = {bbox[0]};
orig_y2 = {bbox[3]};

module design_2d() {{
    translate([0, 0])
    scale([scale_f, scale_f, 1])
    translate([-orig_x1, -orig_y2])
    import("design.svg");
}}

module base_2d() {{
    import("base.svg");
}}

module eyelet() {{
    // 重心から真上の端(top_x, top_y)に向けてアイレットを設置
    translate([{top_x}, {top_y}]) {{
        difference() {{
            circle(r={EYELET_OUTER_RAD});
            circle(r={EYELET_HOLE_RAD});
        }}
    }}
    // ネック部分（土台とアイレットを滑らかにつなぐ長方形）
    translate([{top_x - EYELET_OUTER_RAD}, {top_y - 2}])
        square([{EYELET_OUTER_RAD * 2}, 2]);
}}

// 3Dモデルの結合
union() {{
    // 1. 土台＋アイレットの押し出し
    linear_extrude(height = base_h) {{
        base_2d();
        eyelet();
    }}
    
    // 2. デザイン部（浮き彫り）の押し出し
    translate([0, 0, base_h]) {{
        linear_extrude(height = design_h) {{
            design_2d();
        }}
    }}
}}
"""
    
    with open(scad_path, "w", encoding="utf-8") as f:
        f.write(scad_code)
        
    print("4. OpenSCADによるSTLレンダリングを開始...")
    try:
        # コマンドラインからOpenSCADを実行してSTLを生成
        result = subprocess.run(
            [OPENSCAD_PATH, "-o", stl_path, scad_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"✨ 成功しました！ STLファイルが生成されました: {stl_path}")
        else:
            print("❌ OpenSCADのレンダリング中にエラーが発生しました:")
            print(result.stderr)
            print("\n【ヒント】システムパスに 'openscad' が通っていない可能性があります。コード内の 'OPENSCAD_PATH' を絶対パスに書き換えてみてください。")
    except FileNotFoundError:
        print("❌ OpenSCADがシステムで見つかりませんでした。")
        print("OPENSCAD_PATH の設定を確認するか、OpenSCADをインストールしてください。")
        print(f"一時ファイル（.scad や .svg）は {OUTPUT_DIR} に保存されています。")

if __name__ == "__main__":
    main()