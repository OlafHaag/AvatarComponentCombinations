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
                    Dict,
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


def parse_img_name(img_name: str, sep: str = "-") -> Dict:
    """Extract parts of an image name and map them to tags.

    Tags are: type, skeleton, theme, variant, mesh, region, map.
    Names must consist of these tags in that order connected by a seperator.
    Names are parsed from start to end. If a name contains fewer tags, defaults will be set.

    :param file_name: Image name, with or without its extension.
    :type file_name: str
    :param sep: Character that seperates tags in the name.
    :types sep: str
    :return: Mapping of tags to values found in the image name.
    :rtype: Dict
    """
    # e.g.: "outfit-f-casual-01-v2-bottom-R.jpg"
    parts = img_name.lower().split(".")[0].split(sep)
    tags = ["type", "skeleton", "theme", "variant", "mesh", "region", "map"]
    # Map image name parts to the tags.
    props = dict(zip(tags, parts))
    # Set defaults if a tag is missing.
    props.setdefault("type", "undefined")
    props.setdefault("skeleton", "x")
    props.setdefault("theme", "generic")
    props.setdefault("variant", "01")  # Maps set.
    props.setdefault("mesh", "v1")  # UV Map variant?
    props.setdefault("region", "undefined")
    props.setdefault("map", "D")  # Diffuse/Albedo map is most likely.
    return props
