from mdi_convex import mdi_convex
from render_union import render_union

def generate(name):
    mdi_convex("mdi_svg", name, "svg_with_base")
    render_union(name)


def main():
    import os
    import random
    icons = os.listdir("mdi_svg")

    # t = icons[3420]
    # name = t[:-4]
    # name = "movie-minus-outline"
    # print(name)
    # generate(name)
    # exit(0)

    targets = random.sample(icons, 10)
    # targets = ['truck-remove-outline.svg', 'hamburger-plus.svg', 'diving-flippers.svg', 'view-compact.svg', 'parking.svg']
    for t in targets: #all .svg
        name = t[:-4]
        print(name)
        generate(name)
        os.remove(f"./svg_with_base/{name}.svg")
        os.remove(f"./svg_with_base/{name}_base.svg")
        
    print(targets)

if __name__ == "__main__" :
    main()