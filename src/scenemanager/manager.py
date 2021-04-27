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
from typing import (Optional,
                    Union,
                    Dict,
                    List,
                    Generator,
                    )
import bpy
from bpy.types import Key

from . import materials as mops  # Kinda like Houdini lingo :)
from . import objects as objops
from .. import file_ops as fops


# ToDo: Split manager into smaller files by function domain (e.g. collection/properties related, operators).

# Create new helper-class to transport messages from functions to operators for displaying them in the GUI.
Feedback = namedtuple("Feedback", ["type", "msg"])


###########################################################################################
# Scene initialization. ###################################################################
###########################################################################################

def create_new_scene(scene_name: str = 'Avatar Component Combinations') -> bpy.types.Scene:
    """Create a new scene, name it, and make it active.

    :param scene_name: New name for the scene, defaults to 'Avatar Component Combinations'
    :type scene_name: str, optional
    :return: The new scene object.
    :rtype: bpy.types.Scene
    """
    # We can't guarantee the name. If a scene with that name already exists, a suffix is appended. Keep a reference.
    new_scene = bpy.data.scenes.new(scene_name)
    bpy.context.window.scene = new_scene
    return new_scene


def create_initial_collections(scene: Optional[bpy.types.Scene] = None) -> Dict[str, bpy.types.Collection]:
    """Create source and export collections, as well as failed, ignore, and mandatory subcollections in source.

    :param scene: Scene in which to create new collections.
    :return: Mapping of names to references for new collections.
    :rtype: Dict[str, bpy.types.Collection]
    """
    if not scene:
        scene = bpy.context.scene
    # Create new collections.
    src_collection = bpy.data.collections.new('src')
    src_collection.hide_render = True
    failed_collection = bpy.data.collections.new('_failed')
    ignore_collection = bpy.data.collections.new('_ignore')
    ignore_collection.hide_viewport = True
    mandatory_collection = bpy.data.collections.new('_mandatory')
    export_collection = bpy.data.collections.new('export')
    # Link newly created collections to the respective parent.
    scene.collection.children.link(src_collection)
    src_collection.children.link(failed_collection)
    src_collection.children.link(ignore_collection)
    src_collection.children.link(mandatory_collection)
    scene.collection.children.link(export_collection)
    # Color them for easy identification.
    src_collection.color_tag = 'COLOR_05'
    failed_collection.color_tag = 'COLOR_01'  # Give red warning color.
    ignore_collection.color_tag = 'COLOR_02'
    mandatory_collection.color_tag = 'COLOR_03'
    export_collection.color_tag = 'COLOR_04'  # Greenlit for export.

    # Collection names are not guaranteed. Keep a mapping between intended names and collection references.
    collections = {"src": src_collection,
                   "_failed": failed_collection,
                   "_ignore": ignore_collection,
                   "_mandatory": mandatory_collection,
                   "export": export_collection}
    return collections


def create_collections(names: List[str],
                       parent: Optional[bpy.types.Collection] = None) -> Dict[str, bpy.types.Collection]:
    """Create collections from a list of names and return their instances.

    Collections can be created as children of a given parent collection.
    The names given as input are not guaranteed if a collection of that name already exists.

    :param names: List of names for new collections.
    :type names: List[str]
    :param parent: Parent collection for new collections, defaults to None.
    :type parent: Optional[bpy.types.Collection], optional
    :return: Mapping of intended names to references for newly created collections.
    :rtype: Dict[str, bpy.types.Collection]
    """
    collections = {n: bpy.data.collections.new(n) for n in names}
    # Make sure we link the collections to a parent.
    if not parent:
        parent = bpy.context.scene.collection  # "Master Collection" of current scene.
    for collection in collections.values():
        parent.children.link(collection)

    return collections


def set_collection_map_as_property(scene: bpy.types.Scene, collection_map: Dict[str, bpy.types.Collection]) -> bool:
    """Save a mapping between intended name of a collection and its reference as a scene property.

    Clears any previous data in the property.

    :param scene: Scene for which to save the name to collection map as a property.
    :type scene: bpy.types.Scene
    :param collection_map: A mapping between an intended name for a collection and its reference.
    :type collection_map: Dict[str, bpy.types.Collection]
    :return: Success. Whether all collections in the mapping actually belonged to the scene.
    :rtype: bool
    """
    # Make sure the collections in the map belong to this scene.
    scene_collections = set(objops.traverse_tree(scene.collection))
    is_congruent = not set(collection_map.values()) - scene_collections
    if not is_congruent:
        return False
    # Add scene property items.
    for key, collection in collection_map.items():
        # Overwrite any previous data with same key. Otherwise a new key with the same name is added to the property.
        if key in scene.collection_map.keys():
            col_map = scene.collection_map[key]
            # ToDo: What about old collection in properties, if it's a different one?
        else:
            col_map = scene.collection_map.add()
            col_map.name = key
        col_map.collection = collection
    return True


def set_importfiles_props(scene: Optional[bpy.types.Scene] = None, ext: str = "fbx") -> bool:
    """Gather file-paths and determine components' category.

    :param scene: Scene for which to set custom import-files list property. Needs to have import_root_path property.
    :type scene: bpy.types.Scene
    :param ext: File extension of files to gather, defaults to "fbx".
    :type ext: str, optional
    :return: Success. Whether files paths for import were set to properties.
    :rtype: bool
    """
    if not scene:
        scene = bpy.context.scene
    # Remove old data.
    try:
        scene.import_files.clear()
        root_path = Path(bpy.path.abspath(scene.import_root_path))
    except AttributeError:  # Scene does not have import_path_property. Should be set though by add-on registration.
        return False
    file_paths = fops.get_filepaths(root_path, ext=ext)
    if not file_paths:
        return False  # No files to import
    for path in file_paths:
        import_file = scene.import_files.add()
        import_file.path = str(path)
        import_file.category = path.relative_to(root_path).parts[0]
    return True


def init_import_scene(import_path: Union[Path, str], use_new_scene: bool = True) -> Optional[bool]:
    """Initialize a new scene for avatar component import.

    Create a new scene and populate it with collections, custom properties like a list of files to import.

    :param import_path: Root import folder for batch-importing FBX files with avatar components.
    :type import_path: Union[Path, str]
    :return: Success of setting scene properties for preparing file imports.
    :rtype: bool|None
    """
    if not Path(bpy.path.abspath(str(import_path))).is_dir():
        return None
    if use_new_scene:
        scene = create_new_scene()
    else:
        # Current active scene.
        scene = bpy.context.scene
    try:
        scene.import_root_path = str(import_path)
    except AttributeError:
        return False
    # ToDo: Merge with existing collections if not a new scene?
    init_collections = create_initial_collections(scene)
    if not set_collection_map_as_property(scene, init_collections):
        # Incongruency should not be possible, though, since we just linked the new collections to this scene.
        return False
    # Create component categories.
    categories = fops.get_subfolders(import_path)
    cat_collections = create_collections(categories, parent=init_collections['src'])
    if not set_collection_map_as_property(scene, cat_collections):  # No category collections?
        return False
    if not set_importfiles_props(scene):  # Scene not initialized or no files found?
        return False

    return True


###########################################################################################
# Assets import. ##########################################################################
###########################################################################################

def import_sort_files(context) -> List[Feedback]:
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
        try:
            ret_msgs = fops.load_fbx(context, file_path=import_file.path, ignore_leaf_bones=True)
            if ret_msgs:
                feedback.extend([Feedback(*msg) for msg in ret_msgs])
        except IOError:
            feedback.append(Feedback(type='ERROR', msg=f"File {import_file.path} could not be imported."))
            continue
        file_name = Path(bpy.path.abspath(import_file.path)).stem
        objects = context.active_object.children
        # The first armature that comes in will serve as base for all further imported assets.
        if armature:
            # Get rid of redundant armature. The imported asset is automatically made active.
            objops.remove_object(context.active_object)
        elif context.active_object.type == 'ARMATURE':
            armature = context.active_object
            # Set armature name to include skeleton type (e.g. "f"/"m") as suffix.
            armature_suffix = fops.get_skeleton_type(file_name)
            armature.name = "-".join(("Armature", armature_suffix)).strip("-")  # Strip "-" if there's no suffix.

        for obj in objects:  # There's usually only 1 child.
            # ToDo: Refactor inner loop code to handle a single object into its own function.
            # Save source file property on imported objects.
            obj.src_file = import_file.path
            # In our case the imported meshes don't have very meaningful names. Standardize with file-name tags.
            fname_tags = fops.parse_file_name(file_name)
            if fname_tags["region"] == "undefined":
                fname_tags["region"] = import_file.category
            obj.name = fops.tags_to_name(fname_tags)
            obj.data.name = "_".join(("MESH", obj.name))  # Mesh name.
            # Name materials accoding to their object.
            # ToDo: Handle materials that are shared between objects. Not the case, for now.
            for material in mops.get_materials(obj):  # There's usually only 1 material.
                material.name = "_".join(("MAT", obj.name))  # If the object has multiple materials they'll be numbered.

            # Sort object into a collection, and out of the scene's root collection.
            context.scene.collection.objects.unlink(obj)
            # We want everything to be deformed by the same armature.
            if not objops.set_armature(obj, armature):
                feedback.append(Feedback(type='WARNING', msg=f"Failed to set shared armature for {file_name}."))
                context.scene.collection_map["_failed"].collection.objects.link(obj)
            elif fname_tags["skeleton"] != armature_suffix:
                feedback.append(Feedback(type='WARNING', msg=f"Armature mismatch detected for {file_name}."))
                context.scene.collection_map["_failed"].collection.objects.link(obj)
            elif fname_tags["region"] != import_file.category:
                feedback.append(Feedback(type='WARNING', msg=f"Region mismatch detected for {file_name}."))
                context.scene.collection_map["_failed"].collection.objects.link(obj)
            else:
                # Sort objects into their respective collection by the category associated with their path.
                context.scene.collection_map[import_file.category].collection.objects.link(obj)

    if armature:
        context.scene.collection_map["_mandatory"].collection.objects.link(armature)
        context.scene.collection.objects.unlink(armature)

    # Since we deleted the last active object, set a new one (or None).
    context.view_layer.objects.active = armature
    objops.deselect_all()

    return feedback


def batch_import_components(context, path: Union[Path, str], use_new_scene: bool = True) -> List[Feedback]:
    """[summary]

    :param context: [description]
    :type context: [type]
    :param path: [description]
    :type path: Union[Path, str]
    :param use_new_scene: [description], defaults to True
    :type use_new_scene: bool, optional
    :return: [description]
    :rtype: List[Feedback]
    """
    feedback = list()
    # Save current settings to restore them in new scene later.
    export_path = context.scene.export_path
    n_combinations = context.scene.n_component_combinations
    # Prepare new scene for imports.
    is_initialized = init_import_scene(path, use_new_scene=use_new_scene)
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
        cat_collection_list = list(context.scene.collection_map["src"].collection.children)
        # Don't include failed and ignored components in combinations.
        cat_collection_list.remove(context.scene.collection_map["_ignore"].collection)
        cat_collection_list.remove(context.scene.collection_map["_failed"].collection)
        # Special case "_mandatory" assets.
        mandatory_collection = context.scene.collection_map["_mandatory"].collection
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


def add_combinations_to_export(context, n_combinations: int = 10) -> List[Feedback]:
    """[summary]

    :param context: [description]
    :type context: [type]
    :param n_combinations: [description], defaults to 10
    :type n_combinations: int, optional
    :return: [description]
    :rtype: List[Feedback]
    """
    feedback = list()
    combinations = draw_combinations(context, n_combinations)
    if not combinations:
        feedback.append(Feedback(type='ERROR', msg="Combining avatar components failed."))
        return feedback
    try:
        export_collection = context.scene.collection_map["export"].collection
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


def export_combinations(context, export_path: Union[Path, str]) -> List[Feedback]:
    """[summary]

    :param context: [description]
    :type context: [type]
    :param export_path: [description]
    :type export_path: Union[Path, str]
    :return: [description]
    :rtype: List[Feedback]
    """
    feedback = list()
    try:
        export_collections = context.scene.collection_map['export'].collection.children
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
