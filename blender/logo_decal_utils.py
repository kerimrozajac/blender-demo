"""Reusable Blender helpers for cleaned logo textures and conforming mesh decals."""

from __future__ import annotations

import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector


def _hex_to_linear_rgb(color: str) -> np.ndarray:
    value = color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"Expected an RGB hex color such as #E9BE72, got {color!r}")
    srgb = np.array([int(value[index : index + 2], 16) for index in (0, 2, 4)], dtype=np.float32) / 255
    return np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    )


def create_print_texture(
    source_path: str | Path,
    output_path: str | Path,
    *,
    alpha_threshold: float = 0.31,
    alpha_feather: float = 0.66,
    crop_padding: int = 3,
    recolor_box: tuple[int, int, int, int] | None = None,
    recolor: str = "#E9BE72",
    image_name: str = "Logo_Print",
    pack: bool = True,
) -> bpy.types.Image:
    """Crop transparent margins/glow and optionally recolor an artwork pixel box.

    ``recolor_box`` uses source-image pixel coordinates in (left, top, right, bottom)
    order. Coordinates follow the image's top-left origin, not Blender UV space.
    """
    source_path = Path(source_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Logo image not found: {source_path}")
    if not 0 <= alpha_threshold < 1:
        raise ValueError("alpha_threshold must be in [0, 1)")
    if alpha_feather <= 0:
        raise ValueError("alpha_feather must be greater than zero")
    if crop_padding < 0:
        raise ValueError("crop_padding cannot be negative")

    source = bpy.data.images.load(str(source_path), check_existing=True)
    width, height = source.size
    if source.channels not in (3, 4):
        raise ValueError(f"Expected an RGB or RGBA logo image, got {source.channels} channels")
    pixels = np.asarray(source.pixels[:], dtype=np.float32).reshape(height, width, source.channels)
    if source.channels == 3:
        pixels = np.concatenate((pixels, np.ones((height, width, 1), dtype=np.float32)), axis=2)
    else:
        pixels = pixels.copy()

    alpha = pixels[:, :, 3]
    ys, xs = np.where(alpha > alpha_threshold)
    if len(xs) == 0:
        raise ValueError(
            f"No logo pixels exceed alpha threshold {alpha_threshold:g} in {source_path}"
        )
    x0 = max(0, int(xs.min()) - crop_padding)
    y0 = max(0, int(ys.min()) - crop_padding)
    x1 = min(width, int(xs.max()) + 1 + crop_padding)
    y1 = min(height, int(ys.max()) + 1 + crop_padding)
    pixels = pixels[y0:y1, x0:x1]
    pixels[:, :, 3] = np.clip((pixels[:, :, 3] - alpha_threshold) / alpha_feather, 0, 1)

    if recolor_box:
        left, top, right, bottom = recolor_box
        if left < 0 or top < 0 or right <= left or bottom <= top:
            raise ValueError(f"Invalid recolor_box: {recolor_box!r}")
        source_x = np.arange(x0, x1)[None, :]
        source_y = np.arange(y0, y1)[:, None]
        selected = (
            (source_x >= left)
            & (source_x < right)
            & (source_y >= top)
            & (source_y < bottom)
            & (pixels[:, :, 3] > 0)
        )
        pixels[selected, :3] = _hex_to_linear_rgb(recolor)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = bpy.data.images.new(
        image_name,
        width=pixels.shape[1],
        height=pixels.shape[0],
        alpha=True,
    )
    # Set the color space first: changing it after writing the pixel buffer can reset it.
    image.colorspace_settings.name = "sRGB"
    image.alpha_mode = "STRAIGHT"
    image.pixels.foreach_set(pixels.ravel())
    image.file_format = "PNG"
    image.filepath_raw = str(output_path)
    image.save()
    if pack:
        image.pack()
    return image


def create_surface_decal(
    scene: bpy.types.Scene,
    parent: bpy.types.Object,
    surface: bpy.types.Object,
    image: bpy.types.Image,
    *,
    name: str = "Logo_Decal",
    material_name: str = "Logo_Print_Material",
    camera: bpy.types.Object | None = None,
    sample_frame: int | None = None,
    radial_offset_degrees: float = 0,
    center_radius: float,
    width: float,
    height: float,
    columns: int = 48,
    rows: int = 44,
    ray_height: float = 110,
    surface_offset: float = 0.08,
    roughness: float = 0.78,
    specular: float = 0.12,
) -> bpy.types.Object:
    """Ray-project a UV decal onto a mesh from the parent's local vertical axis.

    The camera direction selects the panel sector; ``radial_offset_degrees`` can
    shift that direction to the measured center between adjacent ribs.
    """
    if parent is surface:
        raise ValueError("The decal parent must not be the surface mesh itself")
    if columns < 2 or rows < 2:
        raise ValueError("Decal grid must have at least two rows and columns")
    if width <= 0 or height <= 0 or center_radius <= 0:
        raise ValueError("Decal width, height, and center radius must be positive")
    if surface_offset < 0:
        raise ValueError("surface_offset cannot be negative")
    camera = camera or scene.camera
    if camera is None:
        raise ValueError("A camera is required to orient the decal toward the viewer")
    if sample_frame is not None:
        scene.frame_set(sample_frame)
    bpy.context.view_layer.update()

    parent_inverse = parent.matrix_world.inverted()
    camera_local = parent_inverse @ camera.matrix_world.translation
    radial = Vector((camera_local.x, camera_local.y, 0))
    if radial.length == 0:
        raise ValueError("Camera is aligned with the parent's local vertical axis")
    radial.normalize()
    radial = Matrix.Rotation(math.radians(radial_offset_degrees), 3, "Z") @ radial
    tangent = Vector((-radial.y, radial.x, 0))

    parent_to_surface = surface.matrix_world.inverted() @ parent.matrix_world
    surface_to_parent = parent_to_surface.inverted()
    ray_direction = (parent_to_surface.to_3x3() @ Vector((0, 0, -1))).normalized()
    vertices: list[tuple[float, float, float]] = []
    texcoords: list[tuple[float, float]] = []
    hit_grid: list[list[int | None]] = []

    for row in range(rows):
        v = row / (rows - 1)
        radius = center_radius + (0.5 - v) * height
        hit_row = []
        for column in range(columns):
            u = column / (columns - 1)
            point_parent = radial * radius + tangent * ((u - 0.5) * width)
            ray_origin = parent_to_surface @ (point_parent + Vector((0, 0, ray_height)))
            hit, location, normal, _ = surface.ray_cast(ray_origin, ray_direction)
            if not hit:
                hit_row.append(None)
                continue

            normal_parent = parent_to_surface.to_3x3().transposed() @ normal
            normal_parent.normalize()
            if normal_parent.z < 0:
                normal_parent.negate()
            point_parent = surface_to_parent @ location + normal_parent * surface_offset
            hit_row.append(len(vertices))
            vertices.append(tuple(point_parent))
            texcoords.append((u, v))
        hit_grid.append(hit_row)

    faces = []
    face_uvs = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            corners = (
                hit_grid[row][column],
                hit_grid[row][column + 1],
                hit_grid[row + 1][column + 1],
                hit_grid[row + 1][column],
            )
            if any(index is None for index in corners):
                continue
            faces.append(corners)
            face_uvs.append([texcoords[index] for index in corners])
    if not faces:
        raise RuntimeError(f"Could not project {image.name!r} onto {surface.name!r}")

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="LogoUV")
    for polygon, face_uv in zip(mesh.polygons, face_uvs):
        polygon.use_smooth = True
        for loop_index, uv in zip(polygon.loop_indices, face_uv):
            uv_layer.data[loop_index].uv = uv

    material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "CLIP"
    texture.label = "Cropped logo print"
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    shader.inputs["Roughness"].default_value = roughness
    specular_socket = shader.inputs.get("Specular IOR Level")
    if specular_socket:
        specular_socket.default_value = specular
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    mesh.materials.append(material)

    decal = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(decal)
    decal.parent = parent
    decal.matrix_parent_inverse = Matrix.Identity(4)
    decal["decal_surface"] = surface.name
    decal["decal_radial_offset_degrees"] = radial_offset_degrees
    decal["decal_surface_offset"] = surface_offset
    decal["decal_grid"] = f"{columns}x{rows}"
    return decal
