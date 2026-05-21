import subprocess as sp
from pathlib import Path

exe_path = "./OpenSCAD-2021.01-x86-64/openscad-2021.01/openscad.com"

def select_dpi(path, default=15):
    try:
        size = Path(path).stat().st_size
    except OSError:
        return default
    if size > 60000:
        return 48
    if size > 20000:
        return 32
    return default


def render_upper(name):
    mdipath = f"./svg_with_base/{name}.svg"

    dpi = select_dpi(mdipath, default=96)
    script = f"""
    union() {{
    // 上側の SVG を 1 mm 押し出す
    linear_extrude(height = 1, center = false) {{
        import(file = "{mdipath}", center = true, dpi = {dpi});
    }}
    }}
    """
    result = sp.run([exe_path, "-o", f"./stl/{name}.stl", "./blank", "-D", script],
        stderr=sp.PIPE,
        stdout=sp.PIPE,
        text=True,)

    print("OpenSCAD 出力:")
    print(result.stdout)


def render_bottom(name):

    basepath = f"./svg_with_base/{name}_base.svg"
    dpi_base = select_dpi(basepath, default=32)

    script = f"""
    union() {{
    // 下側の SVG を 2 mm 押し出し、下方向に配置
        translate([0, 0, -2]) {{
            linear_extrude(height = 2, center = false) {{
                import(file = "{basepath}", center = true, dpi = {dpi_base});
            }}
        }}
    }}
    """
    result = sp.run([exe_path, "-o", f"./stl/{name}.stl", "./blank", "-D", script],
        stderr=sp.PIPE,
        stdout=sp.PIPE,
        text=True,)

    print("OpenSCAD 出力:")
    print(result.stdout)


def render_union(name):

    mdipath = f"./svg_with_base/{name}.svg"
    basepath = f"./svg_with_base/{name}_base.svg"

    dpi_main = select_dpi(mdipath, default=15)
    dpi_base = select_dpi(basepath, default=15)
    script = f"""
    union() {{
    // 上側の SVG を 1 mm 押し出す
    rotate([0, 0, 0]) {{
        linear_extrude(height = 1, center = false) {{
            import(file = "{mdipath}", center = false, dpi = {dpi_main});
        }}
    }}

    // 下側の SVG を 2 mm 押し出し、下方向に配置
    translate([0, 0, -2]) {{
        linear_extrude(height = 2, center = false) {{
            import(file = "{basepath}", center = false, dpi = {dpi_base});
        }}
    }}
    }}
    """


    print(script)

    result = sp.run([exe_path, "-o", f"./stl/{name}.stl", "./blank", "-D", script],
        stderr=sp.PIPE,
        stdout=sp.PIPE,
        text=True,)

    print("OpenSCAD 出力:")
    print(result.stdout)