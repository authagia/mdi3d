import subprocess as sp
from pathlib import Path

def gen_script(path, depth, movez):
    return f"""
    //SVG を押し出し、方向に配置
    translate([0, 0, {movez}]) {{
      linear_extrude(height = {depth}, center = false) {{
        import(file = "{path}", center = true, dpi = 96);
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



stem = "lightbulb-on"

mdipath = f"./svg_with_base/{stem}.svg"
basepath = f"./svg_with_base/{stem}_base.svg"
exe_path = "./OpenSCAD-2021.01-x86-64/openscad-2021.01/openscad.com"

render_3d(mdipath, 1, 0)
render_3d(basepath, 2, -2)
