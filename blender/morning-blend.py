"""Build and render the 8-second Morning Blend coffee-cup animation."""

import math
import os
import sys

import bpy
from mathutils import Vector

NAME = "morning-blend"
WIDTH = 480
HEIGHT = 640
FPS = 24
FRAME_END = 192

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_BLEND = os.path.join(ROOT, "coffee-cup", "Cups.blend")
TEXTURE_DIR = os.path.join(ROOT, "coffee-cup")
FONT_PATH = os.path.join(ROOT, "assets", NAME, "fonts", "ReenieBeanie.ttf")
PROJECT_DIR = os.path.join(ROOT, "renders", NAME)
BLEND_PATH = os.path.join(PROJECT_DIR, "scene.blend")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "blender-frames")


def parse_args():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    frames = None
    if "--frames" in args:
        frames = [int(frame) for frame in args[args.index("--frames") + 1].split(",") if frame]
    return "--no-render" in args, frames


def srgb_to_linear(hex_color):
    channels = [int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ) + (1.0,)


def set_color_management(scene):
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0


def configure_render(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = FRAME_END
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.filepath = os.path.join(OUTPUT_DIR, "frame####")
    scene.render.use_file_extension = True
    scene.render.image_settings.compression = 15
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 64
    scene.render.use_motion_blur = False
    set_color_management(scene)


def relink_cup_textures():
    texture_names = {
        "MM_Coffee_Cup_BaseColor.png": "sRGB",
        "MM_Coffee_Cup_Normal.png": "Non-Color",
        "MM_Coffee_Cup_Roughness.png": "Non-Color",
    }
    for name, color_space in texture_names.items():
        path = os.path.join(TEXTURE_DIR, name)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Required cup texture is missing: {path}")
        image = bpy.data.images.get(name)
        if image is None:
            image = bpy.data.images.load(path, check_existing=True)
        image.filepath = path
        image.colorspace_settings.name = color_space
        image.reload()
        for material in bpy.data.materials:
            if not material.use_nodes or not material.node_tree:
                continue
            for node in material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image and node.image.name.startswith(name):
                    node.image = image


def set_world(scene):
    world = scene.world or bpy.data.worlds.new("Morning Blend Warm Studio")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputWorld")
    background = nodes.new("ShaderNodeBackground")
    background.inputs["Color"].default_value = srgb_to_linear("6B5748")
    background.inputs["Strength"].default_value = 0.34
    world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    world.color = srgb_to_linear("6B5748")[:3]


def make_principled_material(name, hex_color, roughness=0.75):
    material = bpy.data.materials.new(name)
    material.diffuse_color = srgb_to_linear(hex_color)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
    return material, bsdf


def animate_mapping(mapping):
    location = mapping.inputs["Location"]
    for frame, value in ((1, (0.0, 0.0, 0.0)), (FRAME_END, (0.045, -0.035, 0.0))):
        location.default_value = value
        location.keyframe_insert(data_path="default_value", frame=frame)
    action = mapping.id_data.animation_data.action
    if hasattr(action, "fcurves"):
        curves = action.fcurves
    else:
        curves = (
            curve
            for layer in action.layers
            for strip in layer.strips
            for channelbag in strip.channelbags
            for curve in channelbag.fcurves
        )
    for curve in curves:
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "LINEAR"


def make_brick_wall(scene):
    material, bsdf = make_principled_material("Warm Terracotta Brick", "A76A55", 0.88)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (32.0, 42.0, 1.0)
    brick = nodes.new("ShaderNodeTexBrick")
    brick.inputs["Color1"].default_value = srgb_to_linear("875342")
    brick.inputs["Color2"].default_value = srgb_to_linear("754736")
    brick.inputs["Mortar"].default_value = srgb_to_linear("4C3931")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.028
    brick.inputs["Mortar Smooth"].default_value = 0.015
    brick.inputs["Brick Width"].default_value = 0.72
    brick.inputs["Row Height"].default_value = 0.38
    brick.offset = 0.5
    brick.offset_frequency = 2

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.3
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.76, 0.71, 0.66, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (1.0, 0.97, 0.92, 1.0)
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.blend_type = "MULTIPLY"
    multiply.inputs["Fac"].default_value = 0.22
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.17
    bump.inputs["Distance"].default_value = 0.035

    links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(brick.outputs["Color"], multiply.inputs[1])
    links.new(ramp.outputs["Color"], multiply.inputs[2])
    links.new(multiply.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(brick.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    animate_mapping(mapping)

    bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0.0, 2.35, 1.15))
    wall = bpy.context.object
    wall.name = "Seamless Moving Brick Backdrop"
    wall.rotation_euler[0] = math.radians(90.0)
    wall.data.materials.append(material)
    wall["design_note"] = "Procedural staggered terracotta brick with textured mortar."
    for frame, position in (
        (1, (0.0, 2.35, 1.15)),
        (FRAME_END, (-0.22, 2.35, 0.97)),
    ):
        wall.location = position
        wall.keyframe_insert(data_path="location", frame=frame)
    if wall.animation_data and wall.animation_data.action:
        action = wall.animation_data.action
        curves = action.fcurves if hasattr(action, "fcurves") else ()
        for curve in curves:
            for keyframe in curve.keyframe_points:
                keyframe.interpolation = "LINEAR"
    return wall


def add_area_light(scene, name, location, target, power, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.shape = "DISK"
    data.size = size
    data.color = color
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()
    return light


def add_camera(scene):
    data = bpy.data.cameras.new("Portrait Product Camera")
    data.lens = 50.0
    data.sensor_width = 36.0
    camera = bpy.data.objects.new("Portrait Product Camera", data)
    scene.collection.objects.link(camera)
    camera.location = (0.0, -6.25, 1.64)
    target = Vector((0.0, 0.0, 1.36))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    return camera


def iter_action_fcurves(action):
    if hasattr(action, "fcurves"):
        yield from action.fcurves
    else:
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    yield from channelbag.fcurves


def parent_cup_to_pivot(scene):
    cup_parts = [
        bpy.data.objects.get(name)
        for name in (
            "MM_Coffee_Cup_Bottom_Low",
            "MM_Coffee_Cup_Cap_Low",
            "MM_Coffee_Cup_Cup_Low",
            "MM_Coffee_Cup_Holder_Low",
        )
    ]
    missing = [name for name, obj in zip(
        (
            "MM_Coffee_Cup_Bottom_Low",
            "MM_Coffee_Cup_Cap_Low",
            "MM_Coffee_Cup_Cup_Low",
            "MM_Coffee_Cup_Holder_Low",
        ),
        cup_parts,
    ) if obj is None]
    if missing:
        raise RuntimeError(f"Source cup is missing expected mesh objects: {', '.join(missing)}")
    pivot = bpy.data.objects.new("Cup Float and Rotation Pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = (0.0, 0.0, 1.17)
    pivot.empty_display_type = "CIRCLE"
    pivot.empty_display_size = 0.22
    bpy.context.view_layer.update()
    parent_inverse = pivot.matrix_world.inverted()
    for obj in cup_parts:
        local_matrix = obj.matrix_basis.copy()
        obj.parent = pivot
        obj.matrix_parent_inverse = parent_inverse
        obj.matrix_basis = local_matrix

    rotations = (
        (1, (7.0, -5.0, -34.0)),
        (37, (4.5, -3.0, -22.0)),
        (61, (1.1, -0.9, -3.0)),
        (73, (0.0, 0.0, 0.0)),
        (109, (0.45, -0.25, 0.25)),
        (145, (-0.45, 0.25, -0.25)),
        (192, (0.2, 0.0, 0.1)),
    )
    for frame, degrees in rotations:
        pivot.rotation_euler = tuple(math.radians(value) for value in degrees)
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame)
    for frame in range(1, FRAME_END + 1, 12):
        bob = 1.17 + 0.032 * math.sin(2.0 * math.pi * (frame - 1) / 64.0)
        pivot.location = (0.0, 0.0, bob)
        pivot.keyframe_insert(data_path="location", frame=frame)
    if (FRAME_END - 1) % 12:
        frame = FRAME_END
        bob = 1.17 + 0.032 * math.sin(2.0 * math.pi * (frame - 1) / 64.0)
        pivot.location = (0.0, 0.0, bob)
        pivot.keyframe_insert(data_path="location", frame=frame)

    action = pivot.animation_data.action
    for curve in iter_action_fcurves(action):
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "BEZIER"
            keyframe.handle_left_type = "AUTO_CLAMPED"
            keyframe.handle_right_type = "AUTO_CLAMPED"
    return pivot


def create_reveal_geometry(text_object, start_frame, end_frame):
    mesh = text_object.data
    x_min = min(vertex.co.x for vertex in mesh.vertices)
    x_max = max(vertex.co.x for vertex in mesh.vertices)
    if x_max - x_min <= 0.01:
        raise RuntimeError("Jane lettering unexpectedly has no width.")

    group = bpy.data.node_groups.new("Handwritten Name Left-to-Right Reveal", "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = group.nodes
    links = group.links
    geometry_input = nodes.new("NodeGroupInput")
    position = nodes.new("GeometryNodeInputPosition")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    boundary = nodes.new("ShaderNodeValue")
    boundary.name = "Handwriting Reveal Boundary"
    compare = nodes.new("FunctionNodeCompare")
    compare.data_type = "FLOAT"
    compare.operation = "GREATER_THAN"
    delete = nodes.new("GeometryNodeDeleteGeometry")
    delete.domain = "FACE"
    output = nodes.new("NodeGroupOutput")

    links.new(position.outputs["Position"], separate.inputs["Vector"])
    links.new(separate.outputs["X"], compare.inputs[0])
    links.new(boundary.outputs["Value"], compare.inputs[1])
    links.new(geometry_input.outputs["Geometry"], delete.inputs["Geometry"])
    links.new(compare.outputs["Result"], delete.inputs["Selection"])
    links.new(delete.outputs["Geometry"], output.inputs["Geometry"])

    node_tree = group
    for frame, value in (
        (1, x_min - 1.0),
        (start_frame - 1, x_min - 1.0),
        (start_frame, x_min - 0.002),
        (end_frame, x_max + 0.01),
        (FRAME_END, x_max + 0.01),
    ):
        boundary.outputs["Value"].default_value = value
        node_tree.keyframe_insert(
            data_path=f'nodes["{boundary.name}"].outputs[0].default_value', frame=frame
        )
    action = node_tree.animation_data.action
    for curve in iter_action_fcurves(action):
        for keyframe in curve.keyframe_points:
            keyframe.interpolation = "LINEAR"
    modifier = text_object.modifiers.new("Progressive Ink Stroke Mask", "NODES")
    modifier.node_group = group


def add_handwritten_name(scene, pivot):
    font = bpy.data.fonts.load(FONT_PATH)
    font.pack()
    curve = bpy.data.curves.new("Jane Reenie Beanie Ink", "FONT")
    curve.body = "Jane"
    curve.font = font
    curve.size = 0.56
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.space_character = 1.0
    curve.extrude = 0.0015
    curve.bevel_depth = 0.0012
    curve.bevel_resolution = 2
    curve.resolution_u = 16
    text_object = bpy.data.objects.new("Jane — curved cardboard handwriting", curve)
    scene.collection.objects.link(text_object)
    bpy.context.view_layer.objects.active = text_object
    text_object.select_set(True)
    bpy.ops.object.convert(target="MESH")
    text_object = bpy.context.object

    radius = 0.617
    center_z = 1.045
    for vertex in text_object.data.vertices:
        flat_x = vertex.co.x
        ink_depth = vertex.co.z
        angle = flat_x / radius
        vertex.co = (
            radius * math.sin(angle) + math.sin(angle) * ink_depth,
            -radius * math.cos(angle) - 0.006 - math.cos(angle) * ink_depth,
            center_z + vertex.co.y,
        )

    ink, bsdf = make_principled_material("Coffee-Brown Cardboard Ink", "6F432E", 0.78)
    bsdf.inputs["Metallic"].default_value = 0.0
    text_object.data.materials.clear()
    text_object.data.materials.append(ink)
    scene.frame_set(73)
    bpy.context.view_layer.update()
    text_object.parent = pivot
    text_object.matrix_parent_inverse = pivot.matrix_world.inverted()
    text_object.matrix_basis.identity()
    text_object["surface_note"] = "Reenie Beanie mesh warped onto the cup sleeve's cylindrical surface."
    create_reveal_geometry(text_object, start_frame=73, end_frame=109)
    scene.frame_set(1)
    return text_object


def build_scene():
    if not os.path.isfile(SOURCE_BLEND):
        raise FileNotFoundError(f"Source Blender file is missing: {SOURCE_BLEND}")
    if not os.path.isfile(FONT_PATH):
        raise FileNotFoundError(f"Reenie Beanie font is missing: {FONT_PATH}")
    bpy.ops.wm.open_mainfile(filepath=SOURCE_BLEND)
    scene = bpy.context.scene
    configure_render(scene)
    relink_cup_textures()
    set_world(scene)
    make_brick_wall(scene)

    add_area_light(
        scene, "Warm Morning Key", (-3.4, -3.0, 5.1), (0.0, 0.0, 1.1),
        520.0, 3.5, (1.0, 0.79, 0.61),
    )
    add_area_light(
        scene, "Soft Front Fill", (3.5, -3.6, 2.3), (0.0, 0.0, 1.05),
        260.0, 4.2, (1.0, 0.9, 0.77),
    )
    add_area_light(
        scene, "Warm Back Rim", (0.0, 1.0, 4.2), (0.0, 0.0, 1.2),
        300.0, 2.8, (1.0, 0.69, 0.46),
    )
    add_camera(scene)
    pivot = parent_cup_to_pivot(scene)
    add_handwritten_name(scene, pivot)
    scene.render.filepath = os.path.join(OUTPUT_DIR, "frame####")
    scene.frame_set(1)
    return scene


def render(scene, frames):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if frames:
        for frame in frames:
            if not 1 <= frame <= FRAME_END:
                raise ValueError(f"Preview frame {frame} is outside 1–{FRAME_END}.")
            scene.frame_set(frame)
            scene.render.filepath = os.path.join(OUTPUT_DIR, f"preview{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    for old in os.listdir(OUTPUT_DIR):
        if old.startswith("preview") and old.endswith(".png"):
            os.remove(os.path.join(OUTPUT_DIR, old))
    scene.render.filepath = os.path.join(OUTPUT_DIR, "frame####")
    bpy.ops.render.render(animation=True)


def main():
    no_render, frames = parse_args()
    os.makedirs(PROJECT_DIR, exist_ok=True)
    scene = build_scene()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    if not no_render:
        render(scene, frames)


if __name__ == "__main__":
    main()
