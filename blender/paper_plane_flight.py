"""Build, save, and render the paper-plane flight.

Usage:
  Blender --background --factory-startup --python blender/paper_plane_flight.py -- [--frames 1,118,240] [--no-render]
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent.parent
BLEND_PATH = ROOT / "paper_plane_flight.blend"
FRAMES_DIR = ROOT / "my-animation" / "renders" / "paper-plane-blender"

WIDTH, HEIGHT = 640, 480
FPS = 24
FRAME_COUNT = 240


def srgb(hex_color):
    """Convert a hex color to a linear RGB socket value."""
    value = hex_color.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]

    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return tuple(linear(channel) for channel in channels) + (1,)


ORANGE = srgb("FF6A12")
BLUE = srgb("1E4DFF")
VIOLET = srgb("22064A")
SKY_BLUE = srgb("2F78FF")
MID_BLUE = srgb("3A58E4")
PINK = srgb("FF96D0")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    frames = None
    if "--frames" in argv:
        frames = [int(frame) for frame in argv[argv.index("--frames") + 1].split(",")]
    return frames, "--no-render" in argv


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(value):
    value = clamp(value)
    return value * value * (3 - 2 * value)


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


def paper(name, color):
    material = bpy.data.materials.new(name)
    bsdf = principled(material)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    set_input(bsdf, ["Roughness"], 0.94)
    set_input(bsdf, ["Specular IOR Level", "Specular"], 0.12)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 48.0
    noise.inputs["Detail"].default_value = 4.0
    amount = nodes.new("ShaderNodeMath")
    amount.operation = "MULTIPLY"
    amount.inputs[1].default_value = 0.14
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = color
    darker = tuple(channel * 0.86 for channel in color[:3]) + (1,)
    mix.inputs["B"].default_value = darker
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.035
    links.new(noise.outputs["Fac"], amount.inputs[0])
    links.new(amount.outputs["Value"], mix.inputs["Factor"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def new_mesh(name, vertices, faces, materials):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for material in materials:
        obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for polygon, material_index in zip(mesh.polygons, faces):
        polygon.material_index = 0
    bpy.ops.object.shade_flat()
    obj.select_set(False)
    return obj


def assign_materials(obj, indices):
    for polygon, index in zip(obj.data.polygons, indices):
        polygon.material_index = index


def point_faces_up(obj):
    average = Vector((0.0, 0.0, 0.0))
    for polygon in obj.data.polygons:
        average += polygon.normal
    if average.z >= 0:
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def solidify(obj, thickness, material_offset):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    modifier = obj.modifiers.new("Solidify", "SOLIDIFY")
    modifier.thickness = thickness
    modifier.offset = -1
    modifier.use_even_offset = True
    modifier.material_offset = material_offset
    modifier.material_offset_rim = 0
    bpy.ops.object.modifier_apply(modifier="Solidify")
    bpy.ops.object.shade_flat()
    obj.select_set(False)


def build_plane():
    """One folded dart: orange upper wings, blue underside and keel."""
    orange = paper("Orange", ORANGE)
    blue = paper("Blue", BLUE)

    # Nose points along +Y. Tips sit higher than the spine so the center crease reads.
    nose = (0.0, 1.48, 0.0)
    spine = (0.0, 0.02, 0.03)
    left_tip = (-1.12, -0.42, 0.20)
    right_tip = (1.12, -0.42, 0.20)
    left_root = (-0.05, -0.84, 0.04)
    right_root = (0.05, -0.84, 0.04)
    wing_verts = [nose, left_tip, left_root, spine, right_root, right_tip]
    wing_faces = [(0, 1, 2, 3), (0, 3, 4, 5)]
    wings = new_mesh("Wings", wing_verts, wing_faces, [orange, blue])
    assign_materials(wings, [0, 0])
    point_faces_up(wings)
    solidify(wings, 0.022, 1)

    keel_verts = [
        (0.0, 1.20, -0.01),
        (0.0, -0.48, 0.02),
        (0.0, 0.28, -0.22),
        (0.0, -0.22, -0.16),
    ]
    keel = new_mesh("Keel", keel_verts, [(0, 2, 3, 1)], [blue])
    solidify(keel, 0.018, 0)

    root = bpy.data.objects.new("PaperPlane", None)
    bpy.context.collection.objects.link(root)
    wings.parent = root
    keel.parent = root
    root.rotation_mode = "QUATERNION"
    return root


def build_world(scene):
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    background = next(node for node in nodes if node.type == "BACKGROUND")
    background.inputs["Strength"].default_value = 1.0

    coord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coord.outputs["Window"], separate.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "B_SPLINE"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = SKY_BLUE
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = VIOLET
    mid = ramp.color_ramp.elements.new(0.46)
    mid.color = MID_BLUE
    high = ramp.color_ramp.elements.new(0.74)
    high.color = srgb("4C2490")
    links.new(separate.outputs["Y"], ramp.inputs["Fac"])

    # Soft pink band near the lower third, where the horizon sits.
    delta = nodes.new("ShaderNodeMath")
    delta.operation = "SUBTRACT"
    delta.inputs[1].default_value = 0.30
    links.new(separate.outputs["Y"], delta.inputs[0])
    absolute = nodes.new("ShaderNodeMath")
    absolute.operation = "ABSOLUTE"
    links.new(delta.outputs["Value"], absolute.inputs[0])
    width = nodes.new("ShaderNodeMath")
    width.operation = "DIVIDE"
    width.inputs[1].default_value = 0.20
    links.new(absolute.outputs["Value"], width.inputs[0])
    invert = nodes.new("ShaderNodeMath")
    invert.operation = "SUBTRACT"
    invert.inputs[0].default_value = 1.0
    links.new(width.outputs["Value"], invert.inputs[1])
    limited = nodes.new("ShaderNodeClamp")
    links.new(invert.outputs["Value"], limited.inputs["Value"])
    soft = nodes.new("ShaderNodeMath")
    soft.operation = "POWER"
    soft.inputs[1].default_value = 1.7
    links.new(limited.outputs["Result"], soft.inputs[0])
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = 0.72
    links.new(soft.outputs["Value"], strength.inputs[0])

    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(strength.outputs["Value"], mix.inputs["Factor"])
    links.new(ramp.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = PINK
    links.new(mix.outputs["Result"], background.inputs["Color"])


def build_lights():
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.4
    sun_data.angle = math.radians(32)
    sun_data.color = (1.0, 0.96, 0.9)
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(52), math.radians(6), math.radians(-38))
    bpy.context.collection.objects.link(sun)

    fill_data = bpy.data.lights.new("Fill", "AREA")
    fill_data.energy = 120
    fill_data.size = 8
    fill_data.color = (0.72, 0.82, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (1.2, -7.5, 0.4)
    fill.rotation_euler = (math.radians(82), 0, math.radians(8))
    bpy.context.collection.objects.link(fill)


def build_camera(scene):
    data = bpy.data.cameras.new("Camera")
    data.type = "PERSP"
    data.lens = 52
    data.sensor_fit = "HORIZONTAL"
    data.sensor_width = 36
    data.clip_start = 0.1
    data.clip_end = 200
    camera = bpy.data.objects.new("Camera", data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera

    focus = bpy.data.objects.new("Focus", None)
    bpy.context.collection.objects.link(focus)
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = focus
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    return camera, focus


def position(u):
    """Left to right, one rising arc, then away from the camera."""
    travel = math.sin(u * math.pi * 0.5)
    x = lerp(-4.8, 3.4, travel)
    z = 0.25 + 1.25 * travel
    away = 1 - math.cos(clamp((u - 0.40) / 0.60) * math.pi * 0.5)
    y = 6.2 * away
    return Vector((x, y, z))


def orientation(u):
    ahead = position(min(u + 0.012, 1.0))
    behind = position(max(u - 0.012, 0.0))
    tangent = (ahead - behind).normalized()
    yaw = math.atan2(tangent.y, tangent.x)
    pitch = math.atan2(tangent.z, math.hypot(tangent.x, tangent.y))

    # Briefly yaw toward the camera (it sits on -Y), then follow the path away.
    look = math.sin(clamp((u - 0.32) / 0.34) * math.pi)
    yaw += math.radians(-48) * look
    pitch += math.radians(4.5) * math.sin(u * math.pi * 2.0) + math.radians(6) * look

    # Gentle glide, with a shallow bank into the turn so the blue underside flashes.
    glide = math.sin(u * math.pi * 2.0) * math.radians(8)
    bank = glide * (1 - 0.55 * look) + math.radians(-16) * look
    return yaw, pitch, bank


def basis(yaw, pitch, bank):
    forward = Vector(
        (
            math.cos(yaw) * math.cos(pitch),
            math.sin(yaw) * math.cos(pitch),
            math.sin(pitch),
        )
    ).normalized()
    world_up = Vector((0.0, 0.0, 1.0))
    right = forward.cross(world_up)
    if right.length < 1e-5:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(forward).normalized()
    cosine, sine = math.cos(bank), math.sin(bank)
    banked_right = (right * cosine - up * sine).normalized()
    banked_up = (right * sine + up * cosine).normalized()
    return banked_right, forward, banked_up


def place(obj, location, right, forward, up, previous):
    matrix = Matrix(
        (
            (right.x, forward.x, up.x, location.x),
            (right.y, forward.y, up.y, location.y),
            (right.z, forward.z, up.z, location.z),
            (0.0, 0.0, 0.0, 1.0),
        )
    )
    obj.matrix_world = matrix
    quaternion = obj.rotation_quaternion.copy()
    if previous is not None and previous.dot(quaternion) < 0:
        quaternion.negate()
    obj.rotation_quaternion = quaternion
    return quaternion.copy()


def camera_pose(u, plane_location):
    """Side follow, swing to a three-quarter front view, then pull back."""
    glance = math.sin(clamp((u - 0.28) / 0.36) * math.pi)
    depart = 1 - math.cos(clamp((u - 0.58) / 0.42) * math.pi * 0.5)
    distance = 7.9 - 1.05 * glance + 4.6 * depart
    # Positive angle swings ahead of the nose. Negative settles behind it.
    angle = math.radians(40) * glance - math.radians(36) * depart
    # Follow the climb only partway, so the arc rises through the frame.
    follow = 1 - 0.42 * u
    anchored_z = plane_location.z * follow
    # Stay above the wings during the turn so the orange top stays visible.
    height = 2.55 + 1.55 * glance + 0.85 * depart
    offset_x = math.sin(angle) * distance * 0.82
    offset_y = -math.cos(angle) * distance
    camera = Vector((plane_location.x + offset_x, plane_location.y + offset_y, anchored_z + height))
    # Look above the plane early, then closer to it so the climb carries it upward.
    focus = Vector((plane_location.x, plane_location.y, anchored_z + lerp(1.05, 0.35, u)))
    return camera, focus, distance


def animate(plane, camera, focus):
    previous = None
    closest = (1, 1e9)
    for frame in range(1, FRAME_COUNT + 1):
        u = (frame - 1) / (FRAME_COUNT - 1)
        location = position(u)
        right, forward, up = basis(*orientation(u))
        previous = place(plane, location, right, forward, up, previous)
        plane.keyframe_insert("location", frame=frame)
        plane.keyframe_insert("rotation_quaternion", frame=frame)

        cam_loc, focus_loc, distance = camera_pose(u, location)
        camera.location = cam_loc
        focus.location = focus_loc
        camera.keyframe_insert("location", frame=frame)
        focus.keyframe_insert("location", frame=frame)
        if distance < closest[1]:
            closest = (frame, distance)
    print("CLOSEST_FRAME", closest[0], "DISTANCE", round(closest[1], 3))


def configure_render(scene):
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    eevee = scene.eevee
    for attr, value in [("taa_render_samples", 16), ("use_shadows", True), ("use_raytracing", False)]:
        if hasattr(eevee, attr):
            try:
                setattr(eevee, attr, value)
            except (TypeError, ValueError):
                pass

    views = [
        item.identifier
        for item in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items
    ]
    print("VIEWS", views)
    for view in ("Standard", "Khronos PBR Neutral", "Raw", "AgX"):
        if view in views:
            scene.view_settings.view_transform = view
            break
        try:
            scene.view_settings.view_transform = view
            break
        except TypeError:
            continue
    print("VIEW_TRANSFORM", scene.view_settings.view_transform)

    image = scene.render.image_settings
    if hasattr(image, "media_type"):
        image.media_type = "IMAGE"
    image.file_format = "PNG"
    image.color_mode = "RGB"
    image.color_depth = "8"
    image.compression = 15
    scene.render.filepath = str(FRAMES_DIR / "frame")
    scene.render.use_file_extension = True
    scene.render.film_transparent = False


def main():
    frames, skip_render = parse_args()
    scene = reset_scene()
    plane = build_plane()
    build_world(scene)
    build_lights()
    camera, focus = build_camera(scene)
    animate(plane, camera, focus)
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
