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
                    )
import bpy


def get_materials(obj: bpy.types.Object) -> List:
    """Get all materials that are hooked up to material slots ofthe given object.

    :param obj: Object
    :type obj: bpy.types.Object
    :return: Materials.
    :rtype: List
    """
    materials = [mat_slot.material for mat_slot in obj.material_slots]
    return materials


def get_img_nodes(material: bpy.types.Material) -> List:
    """Get all Texture Image shader nodes in a material.

    :param material: Blender node material.
    :type material: bpy.types.Material
    :return: Texture Image shader nodes in the material.
    :rtype: List
    """
    tex_nodes = [node for node in material.node_tree.nodes.values() if node.type == 'TEX_IMAGE']
    return tex_nodes


def get_img_filepath(img_node: bpy.types.ShaderNodeTexImage) -> Path:
    """Get the image file-path from a Texture Image shader node.

    :param img_node: Texture Image shader node.
    :type img_node: bpy.types.ShaderNodeTexImage
    :return: Path to the image file set in the node.
    :rtype: Path
    """
    return Path(bpy.path.abspath(img_node.image.filepath))


def replace_img(node: bpy.types.Image, img_path: Path):
    """Replace the image in an image texture node by a new image from disk.

    The previous image will remain in the data.

    :param node: Image Texture Node for which to replace the image.
    :type node: bpy.types.Image
    :param img_path: Filepath to new image.
    :type img_path: Path
    """
    new_img = node.image.copy()
    new_img.name = bpy.path.display_name_from_filepath(str(img_path))
    new_img.filepath = img_path
    try:
        new_img.unpack(method='REMOVE')
    except RuntimeError:
        pass
    new_img.reload()
    new_img.pack()
    node.image = new_img
