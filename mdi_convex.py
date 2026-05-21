import math
from svgpathtools import parse_path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import ConvexHull
from pathlib import Path

def compute_centroid(points):
    # points は [(x, y), ...] のリスト
    n = len(points)
    sum_x = sum(x for x, _ in points)
    sum_y = sum(y for _, y in points)
    return (sum_x / n, sum_y / n)

def scale_polygon(points, center, scale):
    cx, cy = center
    scaled_points = []
    for (x, y) in points:
        new_x = cx + scale * (x - cx)
        new_y = cy + scale * (y - cy)
        scaled_points.append((new_x, new_y))
    scaled_points = np.array(scaled_points)
    return scaled_points

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
    # r1 = 1
    # r2 = 2

    # l = np.array(l)
    # c = np.array(c)
    # r = np.array(r)
    # lc = c - l
    # rc = c - r
    # mag_lc = math.hypot(*lc)
    # mag_rc = math.hypot(*rc)
    
    # # ③ 内角θ（B での角度）の計算
    # dot = lc.dot(rc)
    # theta = math.acos(dot / (mag_lc * mag_rc))
    # dlc = lc.dot((1,0))
    # base_angle = math.acos(dlc / mag_lc)
    # hole_direc = (math.cos(base_angle + theta/2), math.sin(base_angle + theta/2))
    # hole_direc = np.array(hole_direc)
    # hole_d_norm = np.array(hole_direc[::-1])
    # p1 = c - (r1 + r2) * hole_direc
    # p2 = c - r1 * hole_direc - r2 * hole_d_norm
    # p3 = p2 + 2 * 2 * r2 * hole_direc
    # p4 = p3 + 2 * r2 * hole_d_norm
    # p5 = c - r1 * hole_direc + r2 * hole_d_norm

    # return f"M{p1[0]:.2f},{p1[1]:.2f}" \
    #        f"A{r2},{r2} 0 0 1 {p2[0]:.2f}, {p2[1]:.2f}"\
    #        f"L{p3[0]:.2f},{p3[1]:.2f}"\
    #        f"L{p4[0]:.2f},{p4[1]:.2f}"\
    #        f"L{p5[0]:.2f},{p5[1]:.2f}"\
    #        f"A{r2},{r2} 0 0 1 {p1[0]:.2f},{p1[1]:.2f}"\
    #        f"M{c[0]:.2f},{c[1]:.2f}" \
    #        f"A{r1},{r1} 0 1 0 {c[0]-1e-6},{c[1]:.2f}"\
    #        "Z"
           
   

    return  "M12,-5\
a2,2 0 0 0 -2,2\
v8h4v-8\
a2,2 0 0 0 -2,-2\
m0,1\
a1,1 0 1 1 -.000001,0\
Z"



def mdi_convex(src, name, dist):
    srcpath = Path(".", src, f"{name}.svg")
    distpath_icon = Path(".",dist,f"{name}.svg")
    distpath_base = Path(".",dist,f"{name}_base.svg")

    # mdi のアイコンファイルを読み込む（例: emoticon-remove.svg）
    tree = ET.parse(srcpath)
    root = tree.getroot()
    svg_ns = {"svg": "http://www.w3.org/2000/svg"}
    path_element = root.find('.//svg:path', namespaces=svg_ns)

    # path要素が存在するかチェック
    if path_element is not None:
        d_attr = path_element.get('d')
        path = parse_path(d_attr)

    # サンプル点を500点取得する例
    sample_points = []
    N = 500
    for i in range(N+1):
        t = i / N
        point = path.point(t)
        sample_points.append((point.real, point.imag))


    # サンプル点リストから NumPy array を作成
    points_array = np.array(sample_points)

    # 凸包の計算
    hull = ConvexHull(points_array)
    hull_points = points_array[hull.vertices]


    # 重心（centroid）の計算
    centroid = compute_centroid(hull_points)
    print("重心:", centroid)  # 例: (50.0, 50.0) など

    # 拡大率 (例として1.5倍)
    scale_factor = 1.2

    # 重心を中心にしたスケーリング
    scaled_hull = scale_polygon(hull_points, centroid, scale_factor)

    #########
    if False:
        import matplotlib.pyplot as plt

        # 結果のプロット（確認用）
        plt.figure(figsize=(6,6))
        plt.plot(points_array[:,0], points_array[:,1], 'o', label='sample point')
        for simplex in hull.simplices:
            plt.plot(points_array[simplex, 0], points_array[simplex, 1], 'k-')
        plt.fill(scaled_hull[:, 0], scaled_hull[:, 1], 'o', alpha=0.2, label='convex edges')
        plt.plot(scaled_hull[:, 0], scaled_hull[:, 1], 'o', alpha=0.2)
        plt.legend()
        plt.show()
    #########

    R = 2
    T2 = fillet_svg_path(scaled_hull[-3], scaled_hull[-2], scaled_hull[-1], R)[-1]
    d = f"M{T2[0]:.2f} {T2[1]:.2f}"

    for i in  range(len(scaled_hull)):
        near, T1, T2 = fillet_svg_path(scaled_hull[i-2], scaled_hull[i-1], scaled_hull[i], R)
        if near > R:
            d += f"L{T1[0]:.2f},{T1[1]:.2f}" \
                f"A{R},{R} 0 0,1 {T2[0]:.2f},{T2[1]:.2f}"
        else:
            d += f"L{scaled_hull[i-1, 0]:.2f},{scaled_hull[i-1, 1]:.2f}" \

    d += "Z"

    SVG_NAMESPACE = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NAMESPACE)
    # ルートの <svg> 要素を作成
    svg = ET.Element("svg", attrib={
        "viewBox": f"{12 - 12*scale_factor:.2f} {12 - 12*scale_factor:.2f} {12 + 12*scale_factor:.2f} {12 + 12*scale_factor:.2f}",
        "xmlns": SVG_NAMESPACE
    })

    ET.SubElement(svg, "path", attrib={
        "d": d,
        "fill": "white",
        "stroke": "black",
        "stroke-width": "0.1"
    })

    chainhole = open_hole(scaled_hull[1], scaled_hull[2], scaled_hull[3])

    ET.SubElement(svg, "path", attrib={
        "d": chainhole,
        "fill": "white",
        "stroke": "black",
        "stroke-width": "0.1"
    })
    # SVG ツリーを作成し、ファイルに出力する
    basetree = ET.ElementTree(svg)
    basetree.write(distpath_base, encoding="utf-8")


    root.attrib["viewBox"] = f"{12 - 12*scale_factor:.2f} {12 - 12*scale_factor:.2f} {12 + 12*scale_factor:.2f} {12 + 12*scale_factor:.2f}"
    tree.write(distpath_icon, encoding="utf-8")