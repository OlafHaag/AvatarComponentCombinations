# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from pathlib import Path
from typing import (List,
                    Optional,
                    )
import bpy

from .. import file_ops as fops


def get_materials(obj: bpy.types.Object) -> List:
    """Get all materials that are hooked up to material slots ofthe given object.

    :param obj: Object
    :type obj: bpy.types.Object
    :return: Materials.
    :rtype: List
    """
    return [mat_slot.material for mat_slot in obj.material_slots]


def get_img_nodes(material: bpy.types.Material) -> List:
    """Get all Texture Image shader nodes in a material.

    :param material: Blender node material.
    :type material: bpy.types.Material
    :return: Texture Image shader nodes in the material.
    :rtype: List
    """
    return [
        node
        for node in material.node_tree.nodes.values()
        if node.type == 'TEX_IMAGE'
    ]


def replace_img(node: bpy.types.ShaderNodeTexImage, img_path: Path):
    """Replace the image in an image texture node by a new image from disk.

    The previous image will remain in the data.

    :param node: Image Texture Node for which to replace the image.
    :type node: bpy.types.ShaderNodeTexImage
    :param img_path: Filepath to new image.
    :type img_path: Path
    """
    new_img = node.image.copy()
    new_img.name = bpy.path.display_name_from_filepath(str(img_path))
    new_img.filepath = str(img_path)
    try:
        new_img.unpack(method='REMOVE')
    except RuntimeError:
        pass
    new_img.reload()
    new_img.pack()
    node.image = new_img


def get_image_paths(material: bpy.types.Material) -> List[Path]:
    """Get all existing unique paths for image textures found in the material.

    :param material: Material to scan for image textures.
    :type material: bpy.types.Material
    :return: Paths of image textures.
    :rtype: List[Path]
    """
    img_nodes = get_img_nodes(material)
    image_paths = set()
    for node in img_nodes:
        try:
            img_path = fops.get_abs_path(node.image.filepath)
            if img_path.is_file():
                image_paths.add(img_path)
        except AttributeError:
            continue
    return list(image_paths)


def new_material_variant(material: bpy.types.Material,
                         name: str,
                         image_paths: List[Path]) -> Optional[bpy.types.Material]:
    """Duplicate the material and replace images by new images from disk.

    The provided images must only differ in the variant tag in order to match existing image node file-paths.

    :param material: Material to create a variant of.
    :type material: bpy.types.Material
    :param name: Name for the new material.
    :type name: str
    :param image_paths: Paths to image files to replace existing images.
    :type image_paths: List[Path]
    :return: The new material or None, if no images were replaced.
    :rtype: Optional[bpy.types.Material]
    """
    mat = material.copy()
    mat.name = name
    img_nodes = get_img_nodes(mat)
    was_replaced = False
    for node in img_nodes:
        try:
            img_name = bpy.path.basename(node.image.filepath)
        except AttributeError:
            continue
        var_path = fops.find_variant_path(img_name, image_paths)
        if var_path:
            replace_img(node, var_path)
            was_replaced |= True
    if not was_replaced:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
        del mat
        return None
    return mat
