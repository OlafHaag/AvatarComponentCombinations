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

from typing import (Union,
                    List
                    )
from pathlib import Path

try:
    from io_scene_fbx import import_fbx  # Usually comes with Blender.
except ModuleNotFoundError:
    pass  # ToDo: Handle io_scene_fbx not present.


class DummyOperator():
    """Dummy to provide the report method used by import_fbx.load method."""

    def __init__(self):
        self.messages = list()

    def report(self, type, message):
        """Catch messages instead of reporting them."""
        self.messages.append((type.pop(), message))


def load_fbx(context, file_path: Union[Path, str], **keywords) -> List[tuple]:
    """Import FBX file.

    It's discouraged to call operators from scripts. Use low-level API instead.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param file_path: Path to FBX file.
    :type file_path: Union[Path, str]
    :return: Any error messages raised by the FBX import.
    :rtype: List[tuple]
    """
    file_path = keywords.pop('filepath', file_path)
    if isinstance(file_path, Path):
        file_path = str(file_path)

    dummy_op = DummyOperator()
    ret = import_fbx.load(dummy_op, context, filepath=file_path, **keywords)  # Either {'FINISHED'} or {'CANCELLED'}.
    return dummy_op.messages
