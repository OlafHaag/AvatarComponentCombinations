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
                    Union,
                    )

import bpy


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


def get_skeleton_type(file_name: str) -> str:
    """Extract skeleton/armature type from file name.

    :param file_name: The dash ("-") separated name of the file (not the path). Skeleton type is on the second position.
    :type file_name: str
    :return: Designation of the skeleton type.
    :rtype: str
    """
    try:
        skeleton_type = file_name.split("-")[1]
    except IndexError:
        return ""
    return skeleton_type
