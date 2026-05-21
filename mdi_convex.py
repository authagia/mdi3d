import math
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
# from scipy.spatial import ConvexHull
from svg_sampling import extract_points, create_base_svg

TARGET_SIZE_MM = 60.0
OFFSET_MM = 3.0

# def compute_centroid(points):
#     # points は [(x, y), ...] のリスト
#     n = len(points)
#     sum_x = sum(x for x, _ in points)
#     sum_y = sum(y for _, y in points)
#     return (sum_x / n, sum_y / n)

# def scale_polygon(points, center, scale):
#     cx, cy = center
#     scaled_points = []
#     for (x, y) in points:
#         new_x = cx + scale * (x - cx)
#         new_y = cy + scale * (y - cy)
#         scaled_points.append((new_x, new_y))
#     scaled_points = np.array(scaled_points)
#     return scaled_points

def fillet_svg_path(A, B, C, r):
    """
    A, B, C : (x, y) のタプル (B が交点）
    r      : フィレット半径
    戻り値: SVG のパス文字列 (M, L, A コマンドを用いたもの)
    """
    # ① ベクトル BA, BC（B を原点に持ってくる）
    BA = (A[0] - B[0], A[1] - B[1])
    BC = (C[0] - B[0], C[1] - B[1])
    
    # ② BA, BC の大きさ
    mag_BA = math.hypot(*BA)
    mag_BC = math.hypot(*BC)
    
    # ③ 内角θ（B での角度）の計算
    dot = BA[0]*BC[0] + BA[1]*BC[1]
    theta = math.acos(dot / (mag_BA * mag_BC))
    
    # ④ 接点までの距離 t を計算 (必ず t が BA, BC の長さ以下であることを想定する)
    t = r / math.tan(theta / 2)
    
    # ⑤ BA, BC の単位ベクトル
    uBA = (BA[0] / mag_BA, BA[1] / mag_BA)
    uBC = (BC[0] / mag_BC, BC[1] / mag_BC)
    
    # ⑥ 接点 T1, T2 の算出 (B から t だけ移動)
    T1 = (B[0] + t * uBA[0], B[1] + t * uBA[1])
    T2 = (B[0] + t * uBC[0], B[1] + t * uBC[1])
    return (min(mag_BA, mag_BC), T1, T2)

def open_hole(l, c ,r):
    r1 = 1
    r2 = 2

    l = np.array(l)
    c = np.array(c)
    r = np.array(r)
    lc = c - l
    rc = c - r
    mag_lc = math.hypot(*lc)
    mag_rc = math.hypot(*rc)
    
    # ③ 内角θ（B での角度）の計算
    dot = lc.dot(rc)
    theta = math.acos(dot / (mag_lc * mag_rc))
    dlc = lc.dot((1,0))
    base_angle = math.acos(dlc / mag_lc)
    hole_direc = (math.cos(base_angle + theta/2), math.sin(base_angle + theta/2))
    hole_direc = np.array(hole_direc)
    hole_d_norm = np.array(hole_direc[::-1])
    p1 = c - (r1 + r2) * hole_direc
    p2 = c - r1 * hole_direc - r2 * hole_d_norm
    p3 = p2 + 2 * 2 * r2 * hole_direc
    p4 = p3 + 2 * r2 * hole_d_norm
    p5 = c - r1 * hole_direc + r2 * hole_d_norm

    return f"M{p1[0]:.2f},{p1[1]:.2f}" \
           f"A{r2},{r2} 0 0 1 {p2[0]:.2f}, {p2[1]:.2f}"\
           f"L{p3[0]:.2f},{p3[1]:.2f}"\
           f"L{p4[0]:.2f},{p4[1]:.2f}"\
           f"L{p5[0]:.2f},{p5[1]:.2f}"\
           f"A{r2},{r2} 0 0 1 {p1[0]:.2f},{p1[1]:.2f}"\
           f"M{c[0]:.2f},{c[1]:.2f}" \
           f"A{r1},{r1} 0 1 0 {c[0]-1e-6},{c[1]:.2f}"\
           "Z"
           
   

#     return  "M12,-5\
# a2,2 0 0 0 -2,2\
# v8h4v-8\
# a2,2 0 0 0 -2,-2\
# m0,1\
# a1,1 0 1 1 -.000001,0\
# Z"



def mdi_convex(src, name, dist):
    srcpath = Path(".", src, f"{name}.svg")
    distpath_icon = Path(".", dist, f"{name}.svg")
    distpath_base = Path(".", dist, f"{name}_base.svg")

    # SVGを再帰的サンプリングして点群を生成
    points_array, scale_factor, bbox = extract_points(str(srcpath), TARGET_SIZE_MM, sampling_mode='recursive', params={'tol_mm': 0.25, 'max_depth': 12})

    # 凸包のベースSVGを生成
    offset_poly = create_base_svg(points_array, OFFSET_MM, str(distpath_base), join_style='round')

    # 元SVGをスケールして出力
    tree = ET.parse(srcpath)
    root = tree.getroot()
    SVG_NAMESPACE = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NAMESPACE)

    children = list(root)
    for child in children:
        root.remove(child)

    g = ET.SubElement(root, "g")
    g.attrib["transform"] = f"translate({-bbox[0]},{-bbox[1]}) scale({scale_factor})"
    for child in children:
        g.append(child)

    root.attrib["viewBox"] = f"0 0 {TARGET_SIZE_MM:.2f} {TARGET_SIZE_MM:.2f}"
    root.attrib["width"] = f"{TARGET_SIZE_MM}mm"
    root.attrib["height"] = f"{TARGET_SIZE_MM}mm"
    tree.write(distpath_icon, encoding="utf-8", xml_declaration=True)

    # offset_poly の出力は create_base_svg() が distpath_base に書き出している。
    # ここではそのままベース図形として利用するため、追加書き換えは行わない。
