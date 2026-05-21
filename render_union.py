import subprocess as sp

exe_path = "./OpenSCAD-2021.01-x86-64/openscad-2021.01/openscad.com"

def render_upper(name):
    mdipath = f"./svg_with_base/{name}.svg"

    script = f"""
    union() {{
    // 上側の SVG を 1 mm 押し出す
    linear_extrude(height = 1, center = false) {{
        import(file = "{mdipath}", center = true, dpi = 96);
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

    script = f"""
    union() {{
    // 下側の SVG を 2 mm 押し出し、下方向に配置
        translate([0, 0, -2]) {{
            linear_extrude(height = 2, center = false) {{
                import(file = "{basepath}", center = true, dpi = 32);
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

    script = f"""
    union() {{
    // 上側の SVG を 1 mm 押し出す
    linear_extrude(height = 1, center = false) {{
        import(file = "{mdipath}", center = false, dpi = 15);
    }}

    // 下側の SVG を 2 mm 押し出し、下方向に配置
    translate([0, 0, -2]) {{
        linear_extrude(height = 2, center = false) {{
            import(file = "{basepath}", center = false, dpi = 15);
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