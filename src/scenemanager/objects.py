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

from typing import (Any,
                    Generator
                    )
import bpy


def traverse_tree(node: Any):
    """Traverse all children of a directed acyclic graph hierarchy.

    :param node: Current node to traverse from. Needs to have a children attribute.
    :type node: Any
    :yield: Current node.
    :rtype: Generator
    """
    yield node
    for child in node.children:
        yield from traverse_tree(child)


def deselect_all() -> None:
    """Deselect all objects. Use low-level API instead of relying on bpy.ops.object.select_all operator."""
    for obj in bpy.data.objects:
        obj.select_set(False)


def remove_object(obj: bpy.types.Object):
    """Remove object from scene.

    :param obj: Object to remove
    :type obj: bpy.types.Object
    """
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    if obj.users == 0:
        bpy.data.objects.remove(obj)
    del obj


def set_armature(obj: bpy.types.Object, armature: bpy.types.Object) -> bool:
    """Parent armature to object and modify the armature modifier accordingly, if present.

    :param obj: Object to set as a child to the armature.
    :type obj: bpy.types.Object
    :param armature: Armature to set as a parent to the object.
    :type armature: bpy.types.Object
    :return: Whether the objet has an armature modifier or not.
    :rtype: bool
    """
    obj.parent = armature

    for mod in obj.modifiers:  # We expect 1 modifier, but the stack could be empty (static mesh).
        # Assume "Armature" is the only modifier, but the name is not safe because of counter-suffixes.
        if mod.type == 'ARMATURE':
            mod.object = armature
            mod.name = "Armature"
            break
    else:
        return False
    return True
