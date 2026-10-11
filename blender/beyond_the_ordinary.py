"""Build, save and render the "Beyond the Ordinary" torus scene.

Usage:
  Blender --background --factory-startup --python blender/beyond_the_ordinary.py -- [--frames 1,72,144] [--no-render]
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
BLEND_PATH = ROOT / "beyond_the_ordinary.blend"
FRAMES_DIR = ROOT / "my-animation" / "renders" / "beyond-blender"

WIDTH, HEIGHT = 1280, 720
FPS = 24
FRAME_COUNT = 144
MID_FRAME = FRAME_COUNT // 2

TORUS_HEIGHT = 1.6
LIME = (0.56, 1.0, 0.047, 1.0)  # #C5FF3D in linear sRGB
RING_EMISSION = 3.0
RING_PULSE = 9.0

CAM_START_DIST, CAM_END_DIST = 12.5, 10.5
CAM_ORBIT_DEG = 20.0
CAM_HEIGHT_OFFSET = 0.55


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    frames = None
    if "--frames" in argv:
        frames = [int(f) for f in argv[argv.index("--frames") + 1].split(",")]
    return frames, "--no-render" in argv


def smoothstep(t):
    return t * t * (3 - 2 * t)


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


def principled(mat):
    mat.use_nodes = True
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def brushed_silver():
    mat = bpy.data.materials.new("BrushedSilver")
    bsdf = principled(mat)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    set_input(bsdf, ["Base Color"], (0.82, 0.83, 0.85, 1.0))
    set_input(bsdf, ["Metallic"], 1.0)
    set_input(bsdf, ["Roughness"], 0.22)
    set_input(bsdf, ["Anisotropic", "Specular Anisotropic"], 0.6)

    coords = nodes.new("ShaderNodeTexCoord")
    stretch = nodes.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (1.0, 1.0, 180.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 8.0
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    links.new(coords.outputs["Object"], stretch.inputs["Vector"])
    links.new(stretch.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def lime_emission():
    mat = bpy.data.materials.new("LimeRing")
    bsdf = principled(mat)
    set_input(bsdf, ["Base Color"], LIME)
    set_input(bsdf, ["Emission Color", "Emission"], LIME)
    set_input(bsdf, ["Emission Strength"], RING_EMISSION)
    set_input(bsdf, ["Roughness"], 0.3)
    return mat, bsdf.inputs["Emission Strength"]


def charcoal_floor():
    mat = bpy.data.materials.new("CharcoalFloor")
    bsdf = principled(mat)
    set_input(bsdf, ["Base Color"], (0.018, 0.018, 0.02, 1.0))
    set_input(bsdf, ["Roughness"], 0.55)
    return mat


def build_torus():
    major, minor = 0.9, 0.28
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, major_segments=160, minor_segments=64,
    )
    body = bpy.context.active_object
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major + minor, minor_radius=0.026, major_segments=160, minor_segments=16,
    )
    ring = bpy.context.active_object

    silver = brushed_silver()
    lime, emission_input = lime_emission()
    body.data.materials.append(silver)
    ring.data.materials.append(lime)

    bpy.ops.object.select_all(action="DESELECT")
    ring.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    torus = bpy.context.active_object
    torus.name = "Torus"
    bpy.ops.object.shade_smooth()

    # Stand the torus upright so its hole faces the camera.
    torus.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    torus.location = (0, 0, TORUS_HEIGHT)
    torus.rotation_mode = "ZXY"
    return torus, emission_input


def animate_torus(torus, emission_input, glow_light):
    for frame in range(1, FRAME_COUNT + 1):
        t = (frame - 1) / (FRAME_COUNT - 1)
        torus.rotation_euler = (
            math.radians(15) * math.sin(2 * math.pi * t),
            0,
            math.radians(-25 + 60 * t),
        )
        torus.keyframe_insert("rotation_euler", frame=frame)

        pulse = math.exp(-((frame - MID_FRAME) / 9.0) ** 2)
        emission_input.default_value = RING_EMISSION + (RING_PULSE - RING_EMISSION) * pulse
        emission_input.id_data.keyframe_insert(emission_input.path_from_id("default_value"), frame=frame)
        glow_light.data.energy = 4 + 26 * pulse
        glow_light.data.keyframe_insert("energy", frame=frame)


def build_floor():
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.data.materials.append(charcoal_floor())


def area_light(name, location, energy, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    direction = Vector((0, 0, TORUS_HEIGHT)) - light.location
    light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return light


def build_lights(torus):
    area_light("Key", (-4.5, -5.0, 5.0), 450, 4.0)
    area_light("Rim", (4.0, 4.5, 3.5), 500, 3.0, (0.85, 0.92, 1.0))
    area_light("Top", (0, 0, 7.0), 120, 6.0)

    bpy.ops.object.light_add(type="POINT", location=(0, 0, -0.6))
    glow = bpy.context.active_object
    glow.name = "LimeGlow"
    glow.data.color = LIME[:3]
    glow.data.shadow_soft_size = 1.2
    glow.parent = torus
    return glow


def build_world(scene):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    background = next(n for n in nodes if n.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.004, 0.0045, 0.006, 1.0)
    background.inputs["Strength"].default_value = 1.0

    output = next(n for n in nodes if n.type == "OUTPUT_WORLD")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Density"].default_value = 0.004
    volume.inputs["Anisotropy"].default_value = 0.3
    links.new(volume.outputs["Volume"], output.inputs["Volume"])


def build_camera(scene, torus):
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.name = "Camera"
    scene.camera = cam
    cam.data.lens = 50
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = torus
    cam.data.dof.aperture_fstop = 2.8

    track = cam.constraints.new("TRACK_TO")
    track.target = torus
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    for frame in range(1, FRAME_COUNT + 1):
        t = smoothstep((frame - 1) / (FRAME_COUNT - 1))
        dist = CAM_START_DIST + (CAM_END_DIST - CAM_START_DIST) * t
        angle = math.radians(CAM_ORBIT_DEG) * t
        cam.location = (
            dist * math.sin(angle),
            -dist * math.cos(angle),
            TORUS_HEIGHT + CAM_HEIGHT_OFFSET,
        )
        cam.keyframe_insert("location", frame=frame)


def configure_render(scene):
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    eevee = scene.eevee
    for attr, value in [
        ("taa_render_samples", 64),
        ("use_volumetric_shadows", True),
        ("volumetric_tile_size", "4"),
        ("volumetric_samples", 96),
        ("volumetric_end", 40.0),
        ("use_raytracing", True),
        ("use_shadows", True),
    ]:
        if hasattr(eevee, attr):
            try:
                setattr(eevee, attr, value)
            except (TypeError, ValueError):
                pass

    views = [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items]
    for view in ("AgX", "Filmic"):
        if view in views:
            scene.view_settings.view_transform = view
            break
    looks = [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties["look"].enum_items]
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        if look in looks:
            scene.view_settings.look = look
            break

    image = scene.render.image_settings
    if hasattr(image, "media_type"):
        image.media_type = "IMAGE"
    image.file_format = "PNG"
    image.color_mode = "RGB"
    image.color_depth = "8"
    image.compression = 15
    scene.render.film_transparent = False
    scene.render.filepath = str(FRAMES_DIR / "frame")
    scene.render.use_file_extension = True


def main():
    frames, skip_render = parse_args()
    scene = reset_scene()
    torus, emission_input = build_torus()
    build_floor()
    glow = build_lights(torus)
    animate_torus(torus, emission_input, glow)
    build_world(scene)
    build_camera(scene, torus)
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
