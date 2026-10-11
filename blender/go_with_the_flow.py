"""Build, save and render the "Go With the Flow" paper-boat scene.

Usage:
  Blender --background --factory-startup --python blender/go_with_the_flow.py -- [--frames 1,120,240] [--no-render]
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parent.parent
BLEND_PATH = ROOT / "go_with_the_flow.blend"
FRAMES_DIR = ROOT / "my-animation" / "renders" / "origami-river-blender"

WIDTH, HEIGHT = 640, 480
FPS = 24
FRAME_COUNT = 240

# The stream, in the ground plane. The boat pauses at the middle point.
POINTS = [
    (-3.35, -0.9),
    (-2.15, 0.25),
    (-0.95, 0.72),
    (0.05, 0.0),
    (1.05, -0.62),
    (2.2, 0.18),
    (3.35, 0.78),
]
WATER_HALF = 0.46
BOAT_SCALE = 0.52


def srgb(hex_color):
    """Convert a hex color to a linear RGB socket value."""
    value = hex_color.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]

    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return tuple(linear(channel) for channel in channels) + (1,)


CREAM = srgb("F7EDD8")
WATER = srgb("3ECFC6")
WATER_EDGE = srgb("14959A")
LILY = srgb("3AAA98")
FLOWER = srgb("E6B23C")
FLOWER_CENTER = srgb("F4D48A")
BOAT_RED = srgb("D64545")
RIPPLE = srgb("128E93")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    frames = None
    if "--frames" in argv:
        frames = [int(frame) for frame in argv[argv.index("--frames") + 1].split(",")]
    return frames, "--no-render" in argv


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def lerp(a, b, t):
    return a + (b - a) * t


def catmull(t):
    count = len(POINTS)
    if t <= 0:
        return POINTS[0]
    if t >= 1:
        return POINTS[-1]
    scaled = t * (count - 1)
    index = min(int(scaled), count - 2)
    u = scaled - index

    def at(offset):
        return POINTS[min(max(offset, 0), count - 1)]

    p0, p1, p2, p3 = at(index - 1), at(index), at(index + 1), at(index + 2)

    def mix(a, b, c, d):
        return 0.5 * (
            2 * b
            + (-a + c) * u
            + (2 * a - 5 * b + 4 * c - d) * u * u
            + (-a + 3 * b - 3 * c + d) * u * u * u
        )

    return (mix(p0[0], p1[0], p2[0], p3[0]), mix(p0[1], p1[1], p2[1], p3[1]))


def tangent(t):
    ahead = catmull(min(t + 0.004, 1))
    behind = catmull(max(t - 0.004, 0))
    direction = (ahead[0] - behind[0], ahead[1] - behind[1])
    length = math.hypot(*direction) or 1
    return (direction[0] / length, direction[1] / length)


def path_t(frame):
    """Travel to the middle, pause, then continue to the far end."""
    time = frame - 1
    if time < 108:
        return 0.5 * smoothstep(time / 108)
    if time < 140:
        return 0.5
    return 0.5 + 0.5 * smoothstep((time - 140) / (FRAME_COUNT - 1 - 140))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = FRAME_COUNT
    return scene


def principled(material):
    material.use_nodes = True
    return next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")


def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return node.inputs[name]
    return None


def paper(name, color, fiber=0.25):
    material = bpy.data.materials.new(name)
    bsdf = principled(material)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    set_input(bsdf, ["Roughness"], 0.94)
    set_input(bsdf, ["Specular IOR Level", "Specular"], 0.15)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 45.0
    noise.inputs["Detail"].default_value = 6.0
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["Factor"].default_value = fiber * 0.18
    mix.inputs["A"].default_value = color
    darker = tuple(channel * 0.82 for channel in color[:3]) + (1,)
    mix.inputs["B"].default_value = darker
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = fiber * 0.12
    links.new(noise.outputs["Fac"], mix.inputs["Factor"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def new_mesh(name, vertices, faces, material, flat=True):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_flat()
    obj.select_set(False)
    return obj


def solidify(obj, thickness):
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("Solidify", "SOLIDIFY")
    modifier.thickness = thickness
    modifier.use_even_offset = True
    bpy.ops.object.modifier_apply(modifier="Solidify")


def build_water():
    edge = paper("WaterEdge", WATER_EDGE, fiber=0.15)
    surface = paper("Water", WATER, fiber=0.1)
    samples = 56

    def strip(half_width, z, name, material):
        vertices = []
        for index in range(samples + 1):
            t = index / samples
            x, y = catmull(t)
            nx, ny = tangent(t)
            nx, ny = -ny, nx
            vertices.append((x + nx * half_width, y + ny * half_width, z))
            vertices.append((x - nx * half_width, y - ny * half_width, z))
        faces = [(i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2) for i in range(samples)]
        obj = new_mesh(name, vertices, faces, material)
        solidify(obj, 0.055)
        return obj

    strip(WATER_HALF, 0.02, "WaterEdge", edge)
    strip(WATER_HALF * 0.62, 0.04, "Water", surface)


def build_boat():
    def v(x, y, z):
        return (x * BOAT_SCALE, y * BOAT_SCALE, z * BOAT_SCALE)

    # 0 bow, 1 stern, 2-5 gunwales, 6-9 cockpit rim, 10 keel, 11 cabin peak
    vertices = [
        v(0, 1.45, 0.34), v(0, -1.25, 0.3),
        v(-0.78, 0.28, 0.5), v(0.78, 0.28, 0.5),
        v(-0.66, -0.32, 0.46), v(0.66, -0.32, 0.46),
        v(-0.28, 0.4, 0.62), v(0.28, 0.4, 0.62),
        v(-0.22, -0.2, 0.58), v(0.22, -0.2, 0.58),
        v(0, 0.04, 0.0), v(0, 0.05, 1.55),
    ]
    hull = [
        (0, 3, 10), (0, 10, 2), (10, 5, 1), (10, 1, 4), (10, 3, 5), (10, 4, 2),
        (0, 2, 6), (0, 7, 3), (2, 4, 8), (2, 8, 6), (3, 7, 9), (3, 9, 5),
        (1, 8, 4), (1, 5, 9),
    ]
    folds = [(6, 7, 9), (6, 9, 8), (11, 6, 7), (11, 7, 9), (11, 9, 8), (11, 8, 6)]
    boat = new_mesh("Boat", vertices, hull + folds, paper("BoatPaper", BOAT_RED, fiber=0.45))
    boat.data.materials.append(paper("BoatFold", srgb("F0948C"), fiber=0.3))
    for polygon in boat.data.polygons:
        if polygon.index >= len(hull):
            polygon.material_index = 1
    solidify(boat, 0.016)
    boat.rotation_mode = "XYZ"
    return boat


def build_ring():
    segments = 40
    inner, outer = 0.16, 0.2
    vertices = []
    for index in range(segments):
        angle = 2 * math.pi * index / segments
        vertices.append((math.cos(angle) * outer, math.sin(angle) * outer, 0))
        vertices.append((math.cos(angle) * inner, math.sin(angle) * inner, 0))
    faces = []
    for index in range(segments):
        a = index * 2
        b = ((index + 1) % segments) * 2
        faces.append((a, b, b + 1, a + 1))
    material = paper("Ripple", RIPPLE, fiber=0.05)
    ring = new_mesh("Ripple", vertices, faces, material)
    color = set_input(
        principled(material),
        ["Base Color"],
        RIPPLE,
    )
    # paper() already wires Base Color, so animate the mix color that feeds it.
    mix = next(node for node in material.node_tree.nodes if node.type == "MIX")
    return ring, mix.inputs["A"]


def scatter_props():
    pads = []
    flowers = []
    pad_spots = [0.1, 0.24, 0.37, 0.55, 0.66, 0.8, 0.92]
    for index, t in enumerate(pad_spots):
        side = -1 if index % 2 else 1
        x, y = catmull(t)
        nx, ny = tangent(t)
        nx, ny = -ny * side, nx * side
        distance = WATER_HALF + 0.28
        pad = lily_pad()
        pad.location = (x + nx * distance, y + ny * distance, 0.03)
        pad.rotation_euler.z = math.atan2(ny, nx)
        pads.append(pad)
        if index % 2 == 0:
            flower = paper_flower()
            flower.location = (x + nx * (distance + 0.34), y + ny * (distance + 0.34), 0.03)
            flowers.append(flower)
    return pads


def lily_pad():
    mesh_data = bmesh.new()
    count = 9
    center = mesh_data.verts.new((0, 0, 0))
    outer = []
    for index in range(count):
        angle = 2 * math.pi * index / count
        radius = 0.24 * (0.78 if index % 2 else 1)
        outer.append(mesh_data.verts.new((math.cos(angle) * radius, math.sin(angle) * radius, 0)))
    outer[0].co *= 0.35
    for index in range(count):
        mesh_data.faces.new((center, outer[index], outer[(index + 1) % count]))
    mesh = bpy.data.meshes.new("LilyPad")
    mesh_data.to_mesh(mesh)
    obj = bpy.data.objects.new("LilyPad", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(paper("Lily", LILY, fiber=0.3))
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_flat()
    solidify(obj, 0.01)
    obj.select_set(False)
    return obj


def paper_flower():
    parts = []
    material = paper("Flower", FLOWER, fiber=0.2)
    center_material = paper("FlowerCenter", FLOWER_CENTER, fiber=0.1)
    for index in range(5):
        angle = 2 * math.pi * index / 5
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.09, depth=0.2)
        petal = bpy.context.active_object
        petal.data.materials.append(material)
        petal.rotation_euler = (math.radians(75), 0, angle)
        petal.location = (math.cos(angle) * 0.05, math.sin(angle) * 0.05, 0.03)
        bpy.ops.object.shade_flat()
        parts.append(petal)
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.035, depth=0.04, location=(0, 0, 0.05))
    center = bpy.context.active_object
    center.data.materials.append(center_material)
    bpy.ops.object.shade_flat()
    parts.append(center)
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    flower = bpy.context.active_object
    flower.name = "Flower"
    flower.select_set(False)
    return flower


def build_floor_and_lights(scene):
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Backdrop"
    floor.data.materials.append(paper("Cream", CREAM, fiber=0.35))

    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = next(node for node in world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = CREAM
    background.inputs["Strength"].default_value = 0.3

    def area(name, location, energy, size):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.active_object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        light.data.color = (1.0, 0.94, 0.86)
        return light

    area("Key", (-4.0, -5.0, 7.0), 140, 6.0)
    area("Fill", (4.0, -2.0, 5.0), 40, 8.0)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 8))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 1.6
    sun.data.angle = math.radians(18)
    sun.rotation_euler = (math.radians(55), math.radians(8), math.radians(-35))


def build_camera(scene):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    focus = bpy.context.active_object
    focus.name = "Focus"
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.name = "Camera"
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_end = 200
    track = camera.constraints.new("TRACK_TO")
    track.target = focus
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    return camera, focus


def animate(boat, ripples, pads, camera, focus):
    for frame in range(1, FRAME_COUNT + 1):
        progress = (frame - 1) / (FRAME_COUNT - 1)
        t = path_t(frame)
        x, y = catmull(t)
        dx, dy = tangent(t)
        bob = 0.035 * math.sin(frame * 0.42)
        boat.location = (x, y, 0.1 + bob)
        boat.rotation_euler = (
            math.radians(3.5) * math.sin(frame * 0.31),
            math.radians(5) * math.sin(frame * 0.37 + 1),
            math.atan2(dx, dy),
        )
        boat.keyframe_insert("location", frame=frame)
        boat.keyframe_insert("rotation_euler", frame=frame)

        for index, (ring, color) in enumerate(ripples):
            phase = ((frame + index * 14) % 56) / 56
            ring.scale = (0.35 + phase * 2.4, 0.35 + phase * 2.4, 1)
            color.default_value = tuple(lerp(RIPPLE[c], WATER[c], phase) for c in range(4))
            ring.keyframe_insert("scale", frame=frame)
            color.keyframe_insert("default_value", frame=frame)

        for index, pad in enumerate(pads):
            pad.location.x += 0.0  # location is set absolutely below
            origin = pad["origin"]
            pad.location = (
                origin[0] + 0.05 * math.sin(frame * 0.045 + index),
                origin[1] + 0.035 * math.cos(frame * 0.04 + index * 1.7),
                origin[2],
            )
            pad.rotation_euler.z = origin[3] + math.radians(3) * math.sin(frame * 0.05 + index)
            pad.keyframe_insert("location", frame=frame)
            pad.keyframe_insert("rotation_euler", frame=frame)

        if progress < 0.18:
            follow = smoothstep(progress / 0.18)
        elif progress < 0.7:
            follow = 1
        else:
            follow = 1 - smoothstep((progress - 0.7) / 0.3)
        target_x = lerp(0.0, x, follow)
        target_y = lerp(-0.15, y, follow)
        azimuth = math.radians(32 + 8 * smoothstep(progress))
        distance = lerp(9.4, 7.4, follow)
        camera.location = (
            target_x + math.sin(azimuth) * distance,
            target_y - math.cos(azimuth) * distance,
            4.4,
        )
        # Aim past the subject so it sits low and the top of the frame stays cream.
        focus.location = (target_x, target_y + lerp(1.35, 0.7, follow), 0.15)
        zoom = lerp(10.4, 5.4, follow)
        if progress > 0.72:
            zoom = lerp(zoom, 11.2, smoothstep((progress - 0.72) / 0.28))
        camera.data.ortho_scale = zoom
        camera.keyframe_insert("location", frame=frame)
        focus.keyframe_insert("location", frame=frame)
        camera.data.keyframe_insert("ortho_scale", frame=frame)


def configure_render(scene):
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    eevee = scene.eevee
    for attr, value in [("taa_render_samples", 32), ("use_shadows", True), ("use_raytracing", False)]:
        if hasattr(eevee, attr):
            try:
                setattr(eevee, attr, value)
            except (TypeError, ValueError):
                pass

    views = [item.identifier for item in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items]
    for view in ("Standard", "AgX"):
        if view in views:
            scene.view_settings.view_transform = view
            break

    image = scene.render.image_settings
    if hasattr(image, "media_type"):
        image.media_type = "IMAGE"
    image.file_format = "PNG"
    image.color_mode = "RGB"
    image.color_depth = "8"
    image.compression = 15
    scene.render.filepath = str(FRAMES_DIR / "frame")
    scene.render.use_file_extension = True


def main():
    frames, skip_render = parse_args()
    scene = reset_scene()
    build_water()
    boat = build_boat()
    pads = scatter_props()
    for pad in pads:
        pad["origin"] = (*pad.location, pad.rotation_euler.z)
    ripples = []
    for _ in range(4):
        ring, color = build_ring()
        ring.parent = boat
        ripples.append((ring, color))
    build_floor_and_lights(scene)
    camera, focus = build_camera(scene)
    animate(boat, ripples, pads, camera, focus)
    configure_render(scene)

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print("SAVED", BLEND_PATH)
    if skip_render:
        return
    if frames:
        for frame in frames:
            scene.frame_set(frame)
            scene.render.filepath = str(FRAMES_DIR / f"preview{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
    print("RENDER_DONE")


main()
