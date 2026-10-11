"""Build and render the textured umbrella product shot."""

import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from logo_decal_utils import create_surface_decal

NAME = "umbrella-rain"
WIDTH = 480
HEIGHT = 854
FPS = 24
FRAME_END = 168

ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT / "renders" / NAME
BLEND_PATH = PROJECT_DIR / "scene.blend"
OUTPUT_DIR = PROJECT_DIR / "blender-frames"
REVIEW_DIR = PROJECT_DIR / "review-frames"
TEXT_TEXTURE = ROOT / "assets" / NAME / "skyshield-text.png"
TEXT_DECAL_WIDTH = 29.0
TEXT_CENTER_RADIUS = 48.0
ZOOM_START, ZOOM_END = 3.0, 2.65


def parse_args():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    frames = None
    if "--frames" in args:
        frames = [int(frame) for frame in args[args.index("--frames") + 1].split(",") if frame]
    return "--no-render" in args, frames


def find_asset_root():
    candidates = [
        ROOT / "assets" / "umbrella",
        ROOT / "assets" / "morning-blend" / "fonts" / "umbrella",
    ]
    for candidate in candidates:
        if (candidate / "Umbrella.FBX").is_file():
            return candidate
    raise FileNotFoundError(
        "Umbrella.FBX not found in assets/umbrella or assets/morning-blend/fonts/umbrella"
    )


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def create_material(source, name, map_directory, filename_stem, ao_name=None):
    material = source.copy()
    material.name = f"{name}_textured"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    source_shader = next(
        (node for node in nodes if node.type == "BSDF_PRINCIPLED"), None
    )
    preserved = {}
    if source_shader:
        for socket in source_shader.inputs:
            if not socket.is_linked and hasattr(socket, "default_value"):
                try:
                    preserved[socket.name] = socket.default_value[:]
                except TypeError:
                    preserved[socket.name] = socket.default_value

    nodes.clear()
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (520, 100)
    for input_name, value in preserved.items():
        socket = shader.inputs.get(input_name)
        if socket is not None:
            try:
                socket.default_value = value
            except (TypeError, ValueError):
                pass
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (800, 100)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    def load_map(suffix, colorspace):
        path = map_directory / f"{filename_stem}_{suffix}.png"
        if not path.is_file():
            return None
        image = bpy.data.images.load(str(path), check_existing=True)
        image.colorspace_settings.name = colorspace
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        texture.label = suffix
        texture.location = (0, {"BaseColor": 400, "Metallic": 180, "Roughness": 0, "Normal": -200, "Height": -420, "AO": 620}.get(suffix, 0))
        return texture

    base_color = load_map("BaseColor", "sRGB")
    metallic = load_map("Metallic", "Non-Color")
    roughness = load_map("Roughness", "Non-Color")
    normal = load_map("Normal", "Non-Color")
    height = load_map("Height", "Non-Color")
    ambient_occlusion = load_map(ao_name, "Non-Color") if ao_name else None

    if base_color:
        base_input = shader.inputs.get("Base Color")
        if ambient_occlusion:
            multiply = nodes.new("ShaderNodeMixRGB")
            multiply.blend_type = "MULTIPLY"
            multiply.inputs["Fac"].default_value = 0.22
            multiply.location = (300, 500)
            links.new(base_color.outputs["Color"], multiply.inputs[1])
            links.new(ambient_occlusion.outputs["Color"], multiply.inputs[2])
            links.new(multiply.outputs["Color"], base_input)
        else:
            links.new(base_color.outputs["Color"], base_input)
    if metallic:
        links.new(metallic.outputs["Color"], shader.inputs["Metallic"])
    if roughness:
        links.new(roughness.outputs["Color"], shader.inputs["Roughness"])

    normal_output = None
    if normal:
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_map.location = (280, -180)
        links.new(normal.outputs["Color"], normal_map.inputs["Color"])
        normal_output = normal_map.outputs["Normal"]
    if height:
        bump = nodes.new("ShaderNodeBump")
        bump.location = (420, -320)
        bump.inputs["Strength"].default_value = 0.12
        bump.inputs["Distance"].default_value = 0.008
        links.new(height.outputs["Color"], bump.inputs["Height"])
        if normal_output:
            links.new(normal_output, bump.inputs["Normal"])
        normal_output = bump.outputs["Normal"]
    if normal_output:
        links.new(normal_output, shader.inputs["Normal"])

    material.diffuse_color = source.diffuse_color
    return material


def reconnect_textures(asset_root):
    set_one = asset_root / "Textures" / "Textures_01"
    set_two = asset_root / "Textures" / "Textures_02"
    original = bpy.data.materials.get("Umbrella")
    if original is None:
        raise RuntimeError("FBX import did not provide its expected Umbrella material")

    mappings = (
        ("GEO_Connector_Lower", set_one, "Umbrella_Texture_Sets_Connector_Lower", None),
        ("GEO_Connector_Upper", set_one, "Umbrella_Texture_Sets_Connector_Upper", None),
        ("GEO_Handle", set_one, "Umbrella_Texture_Sets_Handle", None),
        ("GEO_Main_Rod", set_one, "Umbrella_Texture_Sets_Main_Rod", None),
        ("GEO_Main_Skeleton", set_one, "Umbrella_Texture_Sets_Main_Skeleton", None),
        ("GEO_Buffer_Spring", set_one, "Umbrella_Texture_Sets_Springs", None),
        ("GEO_Main_Spring", set_one, "Umbrella_Texture_Sets_Springs", None),
        ("GEO_Top_Cloth", set_one, "Umbrella_Texture_Sets_Top_Cloth", None),
        ("GEO_Umbrella_Top", set_one, "Umbrella_Texture_Sets_Umbrella_Material", None),
        ("Inner_Umbrella", set_one, "Umbrella_Texture_Sets_Umbrella_Material", None),
        ("Runner", set_two, "Umbrella_Texture_Sets_02_Runner", "AO"),
    )

    mesh_objects = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.name != "Cube"
    ]
    for obj in mesh_objects:
        mapping = next((entry for entry in mappings if obj.name.startswith(entry[0])), None)
        if mapping is None:
            raise RuntimeError(f"No texture mapping configured for FBX mesh {obj.name!r}")
        _, directory, stem, ao_name = mapping
        if not (directory / f"{stem}_BaseColor.png").is_file():
            raise FileNotFoundError(f"Missing base-color texture for {obj.name}: {directory / stem}")
        material = create_material(original, obj.name, directory, stem, ao_name)
        obj.data.materials.clear()
        obj.data.materials.append(material)
    return mesh_objects


def create_logo_decal(scene, umbrella_root, canopy):
    text = bpy.data.images.load(str(TEXT_TEXTURE), check_existing=True)
    text.colorspace_settings.name = "sRGB"
    text.alpha_mode = "STRAIGHT"
    text.pack()
    width = TEXT_DECAL_WIDTH
    height = width * text.size[1] / text.size[0]
    decal = create_surface_decal(
        scene,
        umbrella_root,
        canopy,
        text,
        name="Umbrella_SkyShield_Text_Decal",
        material_name="SkyShield_Printed_Text",
        sample_frame=132,
        radial_offset_degrees=15,
        center_radius=TEXT_CENTER_RADIUS,
        width=width,
        height=height,
        columns=64,
        rows=24,
        surface_offset=0.08,
    )
    decal["text_texture"] = str(TEXT_TEXTURE)
    scene["skyshield_decal_faces"] = len(decal.data.polygons)
    return decal


def key(obj, frame, rotation=None, location=None):
    if rotation is not None:
        obj.rotation_euler = tuple(math.radians(value) for value in rotation)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if location is not None:
        obj.location = location
        obj.keyframe_insert(data_path="location", frame=frame)


def set_smooth_interpolation(obj, interpolation="BEZIER"):
    animation = obj.animation_data
    if not animation or not animation.action:
        return
    action = animation.action
    curves = []
    if hasattr(action, "fcurves"):
        curves.extend(action.fcurves)
    else:
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    curves.extend(channelbag.fcurves)
    for curve in curves:
        for point in curve.keyframe_points:
            point.interpolation = interpolation
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"


def setup_scene(scene):
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = FRAME_END
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.image_settings.color_depth = "8"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 64
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Umbrella_World")
    scene.world.color = (0.025, 0.045, 0.07)
    scene.world.use_nodes = True
    background = next(node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.025, 0.045, 0.07, 1)
    background.inputs["Strength"].default_value = 0.35
    scene.render.use_overwrite = True
    scene.render.use_compositing = True
    scene.render.use_sequencer = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = max(1, os.cpu_count() or 1)
    scene.camera.data.type = "ORTHO"
    scene.camera.data.ortho_scale = 3.0
    scene.camera.location = (0.0, -4.8, 2.05)
    aim(scene.camera, (0.0, 0.53, 1.25))

    key_data = bpy.data.lights.new("Umbrella_Key", "AREA")
    key_data.energy = 300
    key_data.shape = "DISK"
    key_data.size = 1.55
    key_light = bpy.data.objects.new("Umbrella_Key", key_data)
    scene.collection.objects.link(key_light)
    key_light.location = (-2.25, -2.7, 3.45)
    aim(key_light, (0.0, 0.53, 1.15))
    key_data.use_shadow = True


def build_scene(scene):
    asset_root = find_asset_root()
    bpy.ops.import_scene.fbx(filepath=str(asset_root / "Umbrella.FBX"))
    scene = bpy.context.scene
    umbrella_root = bpy.data.objects.get("GRP_Revised_Umbrella")
    if umbrella_root is None:
        raise RuntimeError("Umbrella.FBX did not contain GRP_Revised_Umbrella")

    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"} or obj.name == "Cube":
            bpy.data.objects.remove(obj, do_unlink=True)

    mesh_objects = reconnect_textures(asset_root)
    world_pivot = umbrella_root.matrix_world.translation.copy()

    yaw = bpy.data.objects.new("Umbrella_World_Yaw", None)
    tilt = bpy.data.objects.new("Umbrella_Tilt", None)
    scene.collection.objects.link(yaw)
    scene.collection.objects.link(tilt)
    yaw.empty_display_type = "CIRCLE"
    tilt.empty_display_type = "PLAIN_AXES"
    yaw.location = world_pivot
    tilt.parent = yaw
    tilt.location = (0, 0, 0)
    bpy.context.view_layer.update()

    original_world = umbrella_root.matrix_world.copy()
    umbrella_root.parent = tilt
    umbrella_root.matrix_parent_inverse = tilt.matrix_world.inverted()
    umbrella_root.matrix_world = original_world
    bpy.context.view_layer.update()

    for frame, yaw_degrees, tilt_degrees, float_z in (
        (1, -16, -23, world_pivot.z),
        (37, -16, -23, world_pivot.z),
        (84, 100, -20, world_pivot.z + 0.015),
        (132, 116, -17, world_pivot.z + 0.025),
        (168, 116, -17, world_pivot.z + 0.02),
    ):
        key(yaw, frame, rotation=(0, 0, yaw_degrees), location=(world_pivot.x, world_pivot.y, float_z))
        key(tilt, frame, rotation=(0, tilt_degrees, 0), location=(0, 0, 0))
    set_smooth_interpolation(yaw)
    set_smooth_interpolation(tilt)

    for obj in mesh_objects:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    scene.camera = bpy.data.objects.new("Umbrella_Camera", bpy.data.cameras.new("Umbrella_Camera"))
    scene.collection.objects.link(scene.camera)
    setup_scene(scene)
    canopy = next(obj for obj in mesh_objects if obj.name.startswith("GEO_Umbrella_Top"))
    create_logo_decal(scene, umbrella_root, canopy)
    for frame, value in ((1, ZOOM_START), (168, ZOOM_END)):
        scene.camera.data.ortho_scale = value
        scene.camera.data.keyframe_insert(data_path="ortho_scale", frame=frame)
    set_smooth_interpolation(scene.camera.data, "LINEAR")

    scene["source_fbx"] = str(asset_root / "Umbrella.FBX")
    scene["texture_root"] = str(asset_root / "Textures")
    scene["texture_connected_meshes"] = len(mesh_objects)
    scene["animation_axis"] = "world Z"
    scene.frame_set(1)
    return mesh_objects


def render(scene, frames):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if frames:
        REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        for frame in frames:
            scene.frame_set(frame)
            scene.render.filepath = str(REVIEW_DIR / f"preview{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    scene.render.filepath = str(OUTPUT_DIR / "frame####")
    bpy.ops.render.render(animation=True)


def main():
    no_render, frames = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    mesh_objects = build_scene(scene)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(
        f"Built {len(mesh_objects)} textured umbrella meshes; "
        f"{sum(len(material.node_tree.nodes) for material in bpy.data.materials if material.use_nodes)} material nodes."
    )
    if not no_render:
        render(scene, frames)


if __name__ == "__main__":
    main()
