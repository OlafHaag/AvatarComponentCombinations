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

from ..scenemanager.materials import parse_img_name


def get_subfolders(parent_path: Union[Path, str]) -> List[str]:
    """Return names of first-level subfolders in given path.

    :param parent_path: Path to the subfolders' parent folder.
    :type parent_path: Union[pathlib.Path, str]
    :return: List of subfolder names.
    :rtype: List[str]
    """
    if isinstance(parent_path, str):
        parent_path = Path(bpy.path.abspath(parent_path))
    # Do not include any hidden folders, usually indicated by starting with ".".
    subfolders = [f.name.lower() for f in parent_path.glob("*/") if f.is_dir() and not f.name.startswith(".")]
    return subfolders


def get_filepaths(parent_path: Union[Path, str], ext: str = "fbx") -> List[Path]:
    """Search for files in a given folder and return their paths.

    :param parent_path: Root folder in which to recursively look for files.
    :type parent_path: Union[Path, str]
    :param ext: File extension of files to gather, defaults to "fbx".
    :type ext: str, optional
    :return: File paths.
    :rtype: List[Path]
    """
    if isinstance(parent_path, str):
        parent_path = Path(bpy.path.abspath(parent_path))
    file_paths = [f for f in parent_path.glob(f"**/**/*.{ext}")]
    return file_paths


def parse_file_name(file_name: str, sep: str = "-") -> Dict:
    """Extract parts of a file name and map them to tags.

    Tags are: type, skeleton, theme, variant, mesh, region.
    File names must consist of these tags in that order connected by a seperator.
    Names are parsed from start to end. If a file name contains fewer tags, defaults will be set.

    :param file_name: File name, with or without its extension.
    :type file_name: str
    :param sep: Character that seperates tags in the name.
    :types sep: str
    :return: Mapping of tags to values found in the file name.
    :rtype: Dict
    """
    # e.g.: "outfit-f-casual-01-v2-bottom.fbx" versus "fullbody-f-set-01.fbx".
    parts = file_name.lower().split(".")[0].split(sep)
    tags = ["type", "skeleton", "theme", "variant", "mesh", "region"]
    # Map file name parts to the tags.
    props = dict(zip(tags, parts))
    # Set defaults if a tag is missing.
    props.setdefault("type", "undefined")
    props.setdefault("skeleton", "x")
    props.setdefault("theme", "generic")
    props.setdefault("variant", "01")  # Map set.
    props.setdefault("mesh", "v1")  # Mesh variant?
    props.setdefault("region", "undefined")
    return props


def tags_to_name(tags: Dict, sep: str = "-") -> str:
    """Form a file name based on a tags-value mapping.

    :param tags: Mapping of tags to values for use in the name.
    :type tags: Dict
    :param sep: Character that will seperate tags in the name.
    :type sep: str
    :return: Descriptor based on tags.
    :rtype: str
    """
    new_name = sep.join((tags["type"],
                         tags["skeleton"],
                         tags["theme"],
                         tags["variant"],
                         tags["mesh"],
                         tags["region"],
                         ))
    return new_name


def get_skeleton_type(file_name: str) -> str:
    """Extract skeleton/armature type from file name.

    :param file_name: The dash ("-") separated name of the file (not the path).
    :type file_name: str
    :return: Designation of the skeleton type.
    :rtype: str
    """
    try:
        skeleton_type = parse_file_name(file_name)["skeleton"]
    except KeyError:
        return ""
    return skeleton_type


def get_img_variants(img_name: str, path: Path) -> List:
    """Find files like this with another variant tag or map-type. Found files are grouped by variant tag.

    :param img_name: Image name to base search on. Must follow naming convention
    <type>-<skeleton>-<theme>-<variant>-<mesh>-<region>-<map>.ext, e.g. outfit-f-casual-01-v2-bottom-R.jpg.
    :type img_name: str
    :param path: Folder path to inspect for images.
    :type path: Path
    :return: Found images grouped by the variant. List of lists.
    :rtype: List
    """
    # Gather tags from name to form a pattern to look for.
    p = parse_img_name(img_name)
    pattern = f"{p['type']}-{p['skeleton']}-{p['theme']}-??-{p['mesh']}-{p['region']}-?.*"  # Vary variant and map.
    variants = path.glob(pattern)  # Includes the current image variant.
    # Group by variant.
    groups = itertools.groupby(variants, lambda x: parse_img_name(x.stem)['variant'])
    grouped_variants = [list(group) for key, group in groups]
    # Todo Exclude current variant? Or are we also looking for other maps (D, A, E, M, R, O, N)?
    return grouped_variants
