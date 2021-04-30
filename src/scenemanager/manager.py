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

from collections import namedtuple
import hashlib
import itertools
from pathlib import Path
import random
from typing import (Union,
                    List,
                    )
import bpy
from bpy.types import Key

from . import materials as mops  # Kinda like Houdini lingo :)
from . import objects as objops
from . import scenesetup as setup
from .. import file_ops as fops
from .. import Tags
from .. import CollNames

MAT_PREFIX = "MAT_"
MESH_PREFIX = "MESH_"

# Create new helper-class to transport messages from functions to operators for displaying them in the GUI.
Feedback = namedtuple("Feedback", ["type", "msg"])


###########################################################################################
# Assets import. ##########################################################################
###########################################################################################

def import_sort_files(context) -> List[tuple]:
    """Import files that are listed in the scene's properties and sort them into collection categories.

    It's assumed that all files have the same armature as a base. Imported assets will share a single armature.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = list()
    armature = None
    for import_file in context.scene.import_files:
        ret_msgs = fops.load_fbx(context, file_path=import_file.path, ignore_leaf_bones=True)
        feedback.extend([Feedback(*msg) for msg in ret_msgs])
        if 'ERROR' in [msg for msg, _ in ret_msgs]:
            continue
        file_name = Path(bpy.path.abspath(import_file.path)).stem
        fname_tags = fops.parse_file_name(file_name)
        # In our case, the imported meshes don't have very meaningful names. Standardize with file-name tags.
        if fname_tags[Tags.REGION] == "undefined":
            fname_tags[Tags.REGION] = import_file.category

        # If there are multiple meshes in the imported file, join them. We only expect single components per file.
        # The imported asset is automatically made active. Expected to be the armature.
        try:
            objects = list(context.active_object.children)
        except AttributeError:  # In case this FBX is empty or animation data only.
            feedback.append(Feedback(type='WARNING', msg=f"No objects imported from {import_file.path}."))
            continue

        if len(objects) > 1:
            obj = objops.join_objects(context, objects)
            if obj is None:
                feedback.append(Feedback(type='WARNING', msg=f"Joining meshes has failed for: {import_file.path}."))
                context.scene.collection_map[CollNames.FAILED].collection.objects.link(context.active_object)
                context.scene.collection.objects.unlink(context.active_object)
                # ToDo: Move children as well? Currently, I have no such data to test on.
                continue
        elif len(objects) == 1:
            obj = objects[0]
        else:  # No meshes, possibly only an armature.
            obj = None

        # The first armature that comes in will serve as base for all further imported assets.
        if armature:
            # Get rid of redundant armature.
            objops.remove_object(context.active_object)
        elif context.active_object.type == 'ARMATURE':
            armature = context.active_object
            # Set armature name to include skeleton type (e.g. "f"/"m") as suffix.
            armature_suffix = fops.get_skeleton_type(file_name)
            armature.name = "-".join(("Armature", armature_suffix)).strip("-")  # Strip "-" if there's no suffix.

        if obj:
            # ToDo: Refactor inner code code to handle a single object into its own function.
            # Save source file property on imported objects.
            obj.src_file = import_file.path
            obj.name = fops.tags_to_name(fname_tags)
            obj.data.name = MESH_PREFIX + obj.name  # Mesh name.
            # Name materials according to their object.
            # ToDo: Handle materials that are shared between objects. Not the case, for now.
            for material in mops.get_materials(obj):  # There's usually only 1 material.
                material.name = MAT_PREFIX + obj.name  # If the object has multiple materials they'll be numbered.

            # Sort object into a collection, and out of the scene's root collection.
            context.scene.collection.objects.unlink(obj)
            # We want everything to be deformed by the same armature.
            if not objops.set_armature(obj, armature):
                feedback.append(Feedback(type='WARNING', msg=f"Failed to set shared armature for {file_name}."))
                context.scene.collection_map[CollNames.FAILED].collection.objects.link(obj)
            elif fname_tags[Tags.SKELETON] != armature_suffix:
                feedback.append(Feedback(type='WARNING', msg=f"Armature mismatch detected for {file_name}."))
                context.scene.collection_map[CollNames.FAILED].collection.objects.link(obj)
            elif fname_tags[Tags.REGION] != import_file.category:
                feedback.append(Feedback(type='WARNING', msg=f"Region mismatch detected for {file_name}."))
                context.scene.collection_map[CollNames.FAILED].collection.objects.link(obj)
            else:
                # Sort objects into their respective collection by the category associated with their path.
                context.scene.collection_map[import_file.category].collection.objects.link(obj)

    if armature:
        context.scene.collection_map[CollNames.MANDATORY].collection.objects.link(armature)
        context.scene.collection.objects.unlink(armature)

    # Since we deleted the last active object, set a new one (or None).
    context.view_layer.objects.active = armature
    objops.deselect_all()

    return feedback


def batch_import_components(context, path: Union[Path, str], use_new_scene: bool = True) -> List[tuple]:
    """Set up the scene and batch-import avatar components.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param path: Root import folder for batch-importing FBX files with avatar components.
    :type path: Union[Path, str]
    :param use_new_scene: Whether to create a new scene or importing, defaults to True
    :type use_new_scene: bool, optional
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = list()
    # Save current settings to restore them in new scene later.
    export_path = context.scene.export_path
    n_combinations = context.scene.n_component_combinations
    # Prepare new scene for imports.
    is_initialized = setup.init_import_scene(path, use_new_scene=use_new_scene)
    if not is_initialized:
        feedback.append(Feedback(type='ERROR', msg="Importing avatar components failed."))
    else:
        # Restore previous settings.
        context.scene.export_path = export_path
        context.scene.n_component_combinations = n_combinations
        import_errors = import_sort_files(context)
        feedback.extend(import_errors)
    if use_new_scene and is_initialized is not None:
        feedback.append(Feedback(type='INFO', msg="Created a new scene. Your old scene is still there!"))
    return feedback


###########################################################################################
# Component combinations. #################################################################
###########################################################################################

def draw_combinations(context, n: int = 10) -> List:
    """Draw N random combinations from scene's source collections categories.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param n: Number of combinations to draw, defaults to 10.
    :type n: int, optional
    :return: List of combination lists.
    :rtype: List
    """
    try:
        cat_collection_list = list(context.scene.collection_map[CollNames.SOURCE].collection.children)
        # Don't include failed and ignored components in combinations.
        cat_collection_list.remove(context.scene.collection_map[CollNames.IGNORE].collection)
        cat_collection_list.remove(context.scene.collection_map[CollNames.FAILED].collection)
        # Special case for mandatory assets in each combination.
        mandatory_collection = context.scene.collection_map[CollNames.MANDATORY].collection
    except KeyError:  # Scene is not setup correctly.
        print("WARNING: Scene is not initialized properly. Abort.")  # ToDo: Proper warning with logging.
        return []

    # Remove the mandatory assets from combinations now and add them to everything later on.
    cat_collection_list.remove(mandatory_collection)
    asset_lists = [collection.objects for collection in cat_collection_list]
    product = itertools.product(*asset_lists)
    # In case some assets are in the mandatory collection as well as in another category, filter out doubles.
    product = [list(set(list(mandatory_collection.objects) + list(c))) for c in product]
    # Randomize arrangements and draw some combinations.
    # This makes sure the combinations are unique and we never draw more than actually exist.
    random.shuffle(product)
    combinations = product[:n]
    return combinations


def add_combinations_to_export(context, n_combinations: int = 10) -> List[tuple]:
    """Draw a number of combinations from avatar components and add them as export collections.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param n_combinations: Number of combinations to create from components, defaults to 10
    :type n_combinations: int, optional
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = list()
    combinations = draw_combinations(context, n_combinations)
    if not combinations:
        feedback.append(Feedback(type='ERROR', msg="Combining avatar components failed."))
        return feedback
    try:
        export_collection = context.scene.collection_map[CollNames.EXPORT].collection
    except KeyError:
        feedback.append(Feedback(type='ERROR', msg="Scene is not initialized properly. Missing export collection."))
        return feedback

    for combination in combinations:
        # Set a name for the new export collection. All objects have the same armature, get its type from the first.
        comp_string = " ".join(sorted([obj.name for obj in combination]))
        suffix = hashlib.blake2s(comp_string.encode(), digest_size=8).hexdigest()  # 16 characters.
        skeleton = fops.get_skeleton_type(combination[0].name)
        collection_name = "-".join(("set", skeleton, suffix))
        new_collection = bpy.data.collections.new(collection_name)
        # Link object to collection.
        for obj in combination:
            new_collection.objects.link(obj)
        export_collection.children.link(new_collection)
    return feedback


def export_combinations(context, export_path: Union[Path, str]) -> List[tuple]:
    """Export combinations to GLB files.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param export_path: Target folder for batch-exporting combinations to GLB files.
    :type export_path: Union[Path, str]
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = list()
    try:
        export_collections = context.scene.collection_map[CollNames.EXPORT].collection.children
    except KeyError:
        feedback.append(Feedback(type='ERROR', msg="Scene is not initialized properly. Missing export collection."))
        return feedback

    if not Path(bpy.path.abspath(str(export_path))).is_dir():
        feedback.append(Feedback(type='ERROR', msg="Export destination is not a directory."))
        return feedback

    for collection in export_collections:
        # Export is based on object selections. First, deselect everything.
        objops.deselect_all()
        # Now only select objects in 1 export collection at any time.
        for obj in collection.all_objects:
            obj.hide_viewport = False
            obj.hide_set(False)
            obj.select_set(True)
        context.view_layer.objects.active = None
        file_path = (Path(bpy.path.abspath(str(export_path))) / collection.name.replace(".", "_")).with_suffix('.glb')
        try:
            # ToDo: Use low-level API for export, not ops.
            bpy.ops.export_scene.gltf(filepath=str(file_path), use_selection=True, check_existing=False)
            feedback.append(Feedback(type='INFO', msg=f"Exported combination to {file_path}."))
        except IOError as e:
            # Warn, an error would abort all other files as well.
            feedback.append(Feedback(type='WARNING', msg=f"Failed to export file {file_path}.\n{str(e)}"))
            continue

    objops.deselect_all()
    context.view_layer.objects.active = None
    return feedback
