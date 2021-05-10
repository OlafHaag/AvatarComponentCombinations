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
                    Generator,
                    List,
                    Optional,
                    )
import bpy

from . import materials as mops
from . import MESH_PREFIX


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


def show_select_objects(objects: List[bpy.types.Object], context: Optional[bpy.types.Context] = None):
    """Select given objects and deselects all others. Unhide selected objects. Disable active object.

    :param objects: Objects to select.
    :type objects: List[bpy.types.Object]
    :param context: Context, defaults to current context. Used to unset active object.
    :type context: Optional[bpy.types.Context], optional
    """
    deselect_all()
    for obj in objects:
        obj.hide_viewport = False
        obj.hide_set(False)
        obj.select_set(True)
    if not context:
        context = bpy.context
    context.view_layer.objects.active = None


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


def join_objects(context, objects: List[bpy.types.Object]) -> Optional[bpy.types.Object]:
    """Join objects without changing selection or active object.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param objects: Objects to join together. The first item will be joined by the others.
    :type objects: List[bpy.types.Object]
    :return: The resultung joined object or None if joining was not successful.
    :rtype: Optional[bpy.types.Object]
    """
    # The join-operator works on selected objects and we don't wat to alter the selection. So change the context.
    ctx = context.copy()
    # We can only join MESH types.
    objs = [obj for obj in objects if obj.type == 'MESH']
    # The join-operator needs an active object. Take the first one.
    try:
        ctx['active_object'] = objs[0]
    except IndexError:
        return None
    ctx['selected_editable_objects'] = objs
    # When there's only 1 element, join returns {'CANCELLED'}. But we're fine with 1 element, proceed.
    bpy.ops.object.join(ctx)
    return ctx['active_object']


def set_object_attributes(obj,
                          src_filepath: str,
                          name: str,
                          mesh_prefix: str = "MESH_",
                          material_prefix: str = "MAT_") -> bool:
    try:
        obj.src_file = src_filepath  # Custom property.
        obj.name = name
        if obj.type == 'MESH':
            obj.data.name = mesh_prefix + obj.name  # Mesh name.
    except AttributeError:
        return False
    # Name materials according to their object.
    for material in mops.get_materials(obj):  # There's usually only 1 material.
        material.name = material_prefix + obj.name  # If the object has multiple materials they'll be numbered.
    return True


def new_object_variant(obj: bpy.types.Object, name: str, materials: List[bpy.types.Material]) -> bpy.types.Object:
    """Duplicate object and assign materials.

    :param obj: Object to create variant for.
    :type obj: bpy.types.Object
    :param name: Name for the new object.
    :type name: str
    :param materials: Materials to assign to the variant. In order of material slots.
    If the number of existing materials exceeds the number of new materials, extra materials are kept assigned.
    :type materials: List[bpy.types.Material]
    :return: New object variant.
    :rtype: bpy.types.Object
    """
    new_obj = obj.copy()
    new_data = new_obj.data.copy()
    new_data.name = MESH_PREFIX + name
    new_obj.data = new_data
    new_obj.name = name
    for i, mat in enumerate(materials):
        if len(new_obj.data.materials) > i:
            # Assign to material slot.
            new_obj.data.materials[i] = mat
        else:
            # No free slot.
            new_obj.data.materials.append(mat)
    return new_obj
