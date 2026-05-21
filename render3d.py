import subprocess as sp
from pathlib import Path


def select_dpi(path, default=96):
    try:
        size = Path(path).stat().st_size
    except OSError:
        return default
    if size > 60000:
        return 192
    if size > 20000:
        return 128
    return default


def gen_script(path, depth, movez):
    dpi = select_dpi(path, default=96)
    return f"""
    //SVG を押し出し、方向に配置
    translate([0, 0, {movez}]) {{
      linear_extrude(height = {depth}, center = false) {{
        import(file = "{path}", center = true, dpi = {dpi});
      }}
    }}
    """

def render_3d(path, depth, movez):
    stem = Path(path).stem
    script = gen_script(path, depth, movez)
    result = sp.run([exe_path, "-o", f"./stl/{stem}.stl", "./blank", "-D", script],
        stderr=sp.PIPE,
        stdout=sp.PIPE,
        text=True,
    )
    print("OpenSCAD 出力:")
    print(result.stdout)



def main():
    stem = "lightbulb-on"
    mdipath = f"./svg_with_base/{stem}.svg"
    basepath = f"./svg_with_base/{stem}_base.svg"
    render_3d(mdipath, 1, 0)
    render_3d(basepath, 2, -2)


if __name__ == "__main__":
    exe_path = "./OpenSCAD-2021.01-x86-64/openscad-2021.01/openscad.com"
    main()
