import math
from svgelements import SVG, Path, Polyline, Polygon as SVGPolygon
import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.ops import unary_union


def _recursive_sample_segment(segment, t0, t1, p0, p1, tol, max_depth, depth=0):
    """Recursively subdivide a path segment between t0 and t1.
    Compare midpoint deviation from the chord; subdivide until within tolerance.
    Returns list of points (including endpoints).
    """
    tm = (t0 + t1) / 2.0
    pm = segment.point(tm)
    mx, my = pm.x, pm.y
    # chord midpoint
    cx, cy = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
    # deviation from chord
    dev = math.hypot(mx - cx, my - cy)
    if dev <= tol or depth >= max_depth:
        return [p1]
    # subdivide
    left = _recursive_sample_segment(segment, t0, tm, p0, (mx, my), tol, max_depth, depth + 1)
    right = _recursive_sample_segment(segment, tm, t1, (mx, my), p1, tol, max_depth, depth + 1)
    return left + right


def sample_path_recursive(element, scale_x, scale_y, x1, y2, tol_mm=0.2, max_depth=12):
    pts = []
    for segment in element:
        try:
            start_p = segment.point(0)
            p0 = ((start_p.x - x1) * scale_x, (y2 - start_p.y) * scale_y)
            # ensure we include the first point
            pts.append(p0)
            end_p = segment.point(1)
            p1 = ((end_p.x - x1) * scale_x, (y2 - end_p.y) * scale_y)

            # tolerance is in same units as scaled coordinates (mm)
            tail = _recursive_sample_segment(segment, 0.0, 1.0, p0, p1, tol_mm, max_depth)
            for p in tail:
                # p may be tuple (mx,my) only for recursively created midpoints; if svgelements Point, convert
                if hasattr(p, 'x') and hasattr(p, 'y'):
                    px = (p.x - x1) * scale_x
                    py = (y2 - p.y) * scale_y
                    pts.append((px, py))
                else:
                    # expect tuple
                    pts.append((p[0], p[1]))
        except Exception:
            # fallback: sample uniformly
            N = 30
            for i in range(N + 1):
                q = segment.point(i / N)
                pts.append(((q.x - x1) * scale_x, (y2 - q.y) * scale_y))
    return pts


def extract_points(svg_path, target_size, sampling_mode='recursive', params=None):
    """Extract points from SVG and scale to target_size (mm).

    sampling_mode: 'recursive' (default) | 'fixed' 
    params: dict of parameters (tol_mm for recursive, N for fixed)
    """
    svg = SVG.parse(svg_path)
    bbox = svg.bbox()
    if not bbox:
        raise ValueError("SVG bounding box not available")
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    scale = target_size / max(width, height)

    points = []
    tol = params.get('tol_mm', 0.2) if params else 0.2
    for element in svg.elements():
        if isinstance(element, Path):
            if sampling_mode == 'recursive':
                pts = sample_path_recursive(element, scale, scale, x1, y2, tol_mm=tol, max_depth=params.get('max_depth',12) if params else 12)
                points.extend(pts)
            else:
                N = params.get('N', 100) if params else 100
                for segment in element:
                    for i in range(N + 1):
                        p = segment.point(i / N)
                        points.append(((p.x - x1) * scale, (y2 - p.y) * scale))
        elif isinstance(element, (Polyline, SVGPolygon)):
            for p in element.points:
                points.append(((p[0] - x1) * scale, (y2 - p[1]) * scale))

    return np.array(points), scale, (x1, y1, x2, y2)


def create_base_svg(points, offset_mm, output_path=None, join_style='round', pad=5):
    """Create convex-hull-based base polygon, apply offset (mm), and optionally write simple SVG.

    join_style: 'round' | 'mitre' | 'bevel'
    """
    if len(points) < 3:
        raise ValueError("Not enough points to build a polygon")

    hull = ConvexHull(points)
    hull_points = points[hull.vertices]
    poly = ShapelyPolygon(hull_points)

    # map join style
    join_map = {'round': 1, 'mitre': 2, 'bevel': 3}
    j = join_map.get(join_style, 1)

    if abs(offset_mm) < 0.1:
        offset_poly = poly
    else:
        try:
            offset_poly = poly.buffer(offset_mm, join_style=j)
            if not offset_poly.is_valid:
                # attempt to fix
                offset_poly = offset_poly.buffer(0)
        except Exception:
            # fallback: no offset
            offset_poly = poly

    # optional write-out
    exterior_coords = list(offset_poly.exterior.coords)
    min_x = min(p[0] for p in exterior_coords) - pad
    min_y = min(p[1] for p in exterior_coords) - pad
    max_x = max(p[0] for p in exterior_coords) + pad
    max_y = max(p[1] for p in exterior_coords) + pad
    svg_width = max_x - min_x
    svg_height = max_y - min_y

    if output_path:
        points_str = " ".join([f"{p[0]},{p[1]}" for p in exterior_coords])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {svg_width} {svg_height}" width="{svg_width}mm" height="{svg_height}mm">\n')
            f.write(f'  <polygon points="{points_str}" fill="black" />\n')
            f.write('</svg>\n')

    return offset_poly
