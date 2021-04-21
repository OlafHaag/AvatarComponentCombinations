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

import itertools
from pathlib import Path
from typing import (List,
                    Dict,
                    Union,
                    )
import bpy


def get_materials(obj: bpy.types.Object) -> List:
    """[summary]

    :param obj: [description]
    :type obj: bpy.types.Object
    :return: [description]
    :rtype: List
    """
    materials = [mat_slot.material for mat_slot in obj.material_slots]
    return materials


def get_img_nodes(material: bpy.types.Material) -> List:
    """[summary]

    :param material: [description]
    :type material: bpy.types.Material
    :return: [description]
    :rtype: List
    """
    tex_nodes = [node for node in material.node_tree.nodes.values() if node.type == 'TEX_IMAGE']
    return tex_nodes


def get_img_filepath(img_node: bpy.types.ShaderNodeTexImage) -> Path:
    """[summary]

    :param img_node: [description]
    :type img_node: bpy.types.ShaderNodeTexImage
    :return: [description]
    :rtype: Path
    """
    return Path(bpy.path.abspath(img_node.image.filepath))


def parse_img_name(img_name: str) -> Dict:
    """[summary]

    :param img_name: Image name without its extension.
    :type img_name: str
    :return: [description]
    :rtype: Dict
    """
    # e.g.: outfit-f-casual-01-v2-bottom-R
    parts = img_name.split("-")
    try:
        props = {"type": parts[0],      # outfit
                 "skeleton": parts[1],  # f
                 "theme": parts[2],     # casual
                 "variant": parts[3],   # 01
                 "v": parts[4],         # v2
                 "region": parts[5],    # bottom
                 "input": parts[6],     # R
                 }
    except IndexError:
        return dict()
    return props


def get_img_variants(img_name: str, path: Path) -> List:
    """[summary]

    :param img_name: [description]
    :type img_name: str
    :param path: [description]
    :type path: Path
    :return: [description]
    :rtype: List
    """
    p = parse_img_name(img_name)
    if not p:
        return list()

    pattern = f"{p['type']}-{p['skeleton']}-{p['theme']}-??-{p['v']}-{p['region']}-?.*"
    variants = path.glob(pattern)  # Includes the current image variant.
    # Group by variant.
    groups = itertools.groupby(variants, lambda x: parse_img_name(x.stem)['variant'])
    grouped_variants = [list(group) for key, group in groups]
    # Todo Exclude current variant.
    return grouped_variants
