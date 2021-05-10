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

import hashlib
import itertools
import random
from collections import namedtuple
from pathlib import Path
from typing import (Dict,
                    List,
                    Optional,
                    Union,
                    )

import bpy

from .. import CollNames, Tags
from .. import file_ops as fops
from . import MESH_PREFIX, MAT_PREFIX
from . import materials as mops  # Kinda like Houdini lingo :)
from . import objects as objops
from . import scenesetup as setup


# Create new helper-class to transport messages from functions to operators for displaying them in the GUI.
Feedback = namedtuple("Feedback", ["type", "msg"])


###########################################################################################
# Assets import. ##########################################################################
###########################################################################################

def get_import_tags(filepath: str, fallback_category: str = str(CollNames.FAILED)) -> Dict:
    """Extract information from a file's name that's about to be imported.

    :param filepath: Path to the import file.
    :type filepath: str
    :param fallback_category: Fallback category into which to sort imported objects, in case it can't be extracted from
    the file name, defaults to the failed import category.
    :type fallback_category: str, optional
    :return: Tags extracted from the filename.
    :rtype: Dict
    """
    file_name = bpy.path.basename(filepath)
    tags = fops.parse_file_name(file_name)
    # In our case, the imported meshes don't have very meaningful names. Standardize with file-name tags.
    if tags[Tags.REGION] == "undefined":
        tags[Tags.REGION] = fallback_category
    return tags


def new_armature_name(name_suffix: str = ""):
    # Set armature name to include skeleton type (e.g. "f"/"m") as suffix.
    return "-".join(("Armature", name_suffix)).strip("-")  # Strip "-" if there's no suffix.


def handle_redundant_armature(candidate: Optional[bpy.types.Object],
                              armature: Optional[bpy.types.Object] = None,
                              new_name: str = "Armature"):

    # Any existing armature will serve as the base for all further imported assets.
    try:
        candidate_is_armature = candidate.type == 'ARMATURE'
    except AttributeError:
        return armature

    if armature and candidate_is_armature:
        # Get rid of redundant armature.
        objops.remove_object(candidate)
    elif candidate_is_armature:
        armature = candidate
        armature.name = new_name
    return armature


def link_obj_to_category(scene: bpy.types.Scene,
                         obj: bpy.types.Object,
                         category: str,
                         exclusive: bool = True) -> bool:
    """Put an object into a collection, and optionally out of any other collection.

    :param scene: Scene with collection map property and respective collections.
    :type scene: bpy.types.Scene
    :param obj: Object to link to a collection matching the category.
    :type obj: bpy.types.Object
    :param category: Name of the collection category in the scene's collection_map property.
    The actual name of the collection may differ.
    :type category: str
    :param exclusive: Whether to link the object exclusively to the given category, defaults to True.
    :type exclusive: bool, optional
    :return: Whether linking was successful.
    :rtype: bool
    """
    if exclusive and obj:
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
    try:
        scene.collection_map[category].collection.objects.link(obj)
    except (AttributeError, KeyError):
        return False
    return True


def sort_objects(scene: bpy.types.Scene, objects: List[bpy.types.Object], categories: List[str]):
    success = True
    for i, obj in enumerate(objects):
        try:
            category = categories[i]
        except IndexError:
            category = CollNames.FAILED
            success = False
        success &= link_obj_to_category(scene, obj, category)
    return success


def import_files(context) -> List[tuple]:
    """Import files that are listed in the scene's properties and sort them into collection categories.

    It's assumed that all files have the same armature as a base. Imported assets will share a single armature.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = []
    armature = None
    assets = []

    for import_file in context.scene.import_files:
        context.view_layer.objects.active = None
        ret_msgs = fops.load_fbx(context, file_path=import_file.path, ignore_leaf_bones=True)
        feedback.extend([Feedback(*msg) for msg in ret_msgs])
        if 'ERROR' in [msg for msg, _ in ret_msgs]:
            continue

        # If there are multiple meshes in the imported file, join them. We only expect single components per file.
        # The imported asset is automatically made active. Expected to be the armature.
        try:
            objects = list(context.active_object.children)
        except AttributeError:  # In case this FBX is empty or animation data only.
            feedback.append(Feedback(type='WARNING', msg=f"No objects imported from {import_file.path}"))
            continue

        obj = objops.join_objects(context, objects)
        if obj is None:  # No meshes, possibly only an armature.
            feedback.append(Feedback(type='WARNING', msg=f"Joining meshes has failed for: {import_file.path}"))
            continue

        file_tags = get_import_tags(import_file.path, import_file.category)
        # In case a new shared armature is set, give it a name.
        armature_name = new_armature_name(name_suffix=file_tags[Tags.SKELETON])
        armature = handle_redundant_armature(context.active_object, armature, new_name=armature_name)

        # Save source file property on imported objects.
        ret = objops.set_object_attributes(obj, import_file.path, fops.tags_to_name(file_tags), MESH_PREFIX, MAT_PREFIX)
        if not ret:
            feedback.append(Feedback(type='WARNING', msg=f"Object properties could not be set for: {import_file.path}"))

        # We want everything to be deformed by the same armature.
        if not objops.set_armature(obj, armature):
            feedback.append(Feedback(type='WARNING', msg=f"Failed to set shared armature for {obj.name}."))
            assets.append((obj, str(CollNames.FAILED)))
        elif armature_name != armature.name:
            feedback.append(Feedback(type='WARNING', msg=f"Armature mismatch detected for {obj.name}."))
            assets.append((obj, str(CollNames.FAILED)))
        elif file_tags[Tags.REGION] != import_file.category:
            feedback.append(Feedback(type='WARNING', msg=f"Region mismatch detected for {obj.name}."))
            assets.append((obj, str(CollNames.FAILED)))
        else:
            assets.append((obj, import_file.category))

    if armature:
        assets.append((armature, str(CollNames.MANDATORY)))

    # Since we deleted the last active object, set a new one (or None).
    context.view_layer.objects.active = armature
    objops.deselect_all()

    return assets, feedback


def load_variants(obj: bpy.types.Object) -> List[bpy.types.Object]:
    materials = mops.get_materials(obj)
    mat_variants = {}
    for mat in materials:
        img_paths = mops.get_image_paths(mat)
        try:
            # Get a random image for now. Assume all image variants of a material are in the same folder.
            img1 = img_paths.pop()
        except IndexError:
            continue
        variant_paths = fops.get_img_variants(img1.stem, img1.parent, exclude_current=True)

        for variant, paths in variant_paths.items():
            mat_name = fops.replace_name_variant(mat.name, variant)
            new_mat = mops.new_material_variant(mat, mat_name, paths)
            if variant in mat_variants:
                mat_variants[variant].append(new_mat)
            else:
                mat_variants[variant] = [new_mat]

    obj_variants = []
    for variant, new_materials in mat_variants.items():
        obj_name = fops.replace_name_variant(obj.name, variant)
        new_obj = objops.new_object_variant(obj, obj_name, new_materials)
        obj_variants.append(new_obj)
    return obj_variants


def batch_import_components(context: bpy.types.Context,
                            path: Union[Path, str],
                            use_new_scene: bool = True,
                            use_variants: bool = True) -> List[tuple]:
    """Set up the scene and batch-import avatar components.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param path: Root import folder for batch-importing FBX files with avatar components.
    :type path: Union[Path, str]
    :param use_new_scene: Whether to create a new scene or importing, defaults to True
    :type use_new_scene: bool, optional
    :param use_variants: Import texture variants, too.
    :type use_variants: bool, optional.
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = []
    # Save current settings to restore them in new scene later.
    export_path = context.scene.export_path
    n_combinations = context.scene.n_component_combinations
    # Prepare new scene for imports.
    is_initialized = setup.init_import_scene(path, use_new_scene=use_new_scene)
    if is_initialized:
        # Restore previous settings.
        context.scene.export_path = export_path
        context.scene.n_component_combinations = n_combinations
        assets, import_errors = import_files(context)
        if use_variants:
            new_assets = []
            for obj, category in assets:
                variants = load_variants(obj)
                new_assets.extend((v, category) for v in variants)
            assets.extend(new_assets)

        objects, categories = zip(*assets)
        feedback.extend(import_errors)
        is_all_sorted = sort_objects(context.scene, objects, categories)
        if not is_all_sorted:
            feedback.append(Feedback(type='WARNING',
                                     msg="Not all components could be sorted into their designated collection."))
    else:
        feedback.append(Feedback(type='ERROR', msg="Importing avatar components failed."))
    if use_new_scene and is_initialized is not None:
        feedback.append(Feedback(type='INFO', msg="Created a new scene. Your old scene is still there!"))
    return feedback


###########################################################################################
# Component combinations. #################################################################
###########################################################################################

def draw_combinations(scene: bpy.types.Scene, n: int = 10) -> List:
    """Draw N random combinations from scene's source collections categories.

    :param scene: Scene with collection map property and respective collections.
    :type scene: bpy.types.Scene
    :param n: Number of combinations to draw, defaults to 10.
    :type n: int, optional
    :return: List of combination lists.
    :rtype: List
    """
    try:
        cat_collection_list = list(scene.collection_map[str(CollNames.SOURCE)].collection.children)
        # Don't include failed and ignored components in combinations.
        cat_collection_list.remove(scene.collection_map[str(CollNames.IGNORE)].collection)
        cat_collection_list.remove(scene.collection_map[str(CollNames.FAILED)].collection)
        # Special case for mandatory assets in each combination.
        mandatory_collection = scene.collection_map[str(CollNames.MANDATORY)].collection
    except (AttributeError, KeyError):  # Scene is not setup correctly.
        print("WARNING: Scene is not initialized properly. Abort.")
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
    return product[:n]


def add_combinations_to_export(scene: bpy.types.Scene, n_combinations: int = 10) -> List[tuple]:
    """Draw a number of combinations from avatar components and add them as export collections.

    :param scene: Scene with collection map property and respective collections.
    :type scene: bpy.types.Scene
    :param n_combinations: Number of combinations to create from components, defaults to 10
    :type n_combinations: int, optional
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = []
    combinations = draw_combinations(scene, n_combinations)
    if not combinations:
        feedback.append(Feedback(type='ERROR', msg="Combining avatar components failed."))
        return feedback
    try:
        export_collection = scene.collection_map[str(CollNames.EXPORT)].collection
    except (AttributeError, KeyError):
        feedback.append(Feedback(type='ERROR', msg="Scene is not initialized properly. Missing export collection."))
        return feedback

    collections = []
    for combination in combinations:
        collection_name = get_combination_name(combination)
        if not collection_name:
            continue
        new_collection = setup.objects_to_collection(combination, collection_name)
        collections.append(new_collection)
    setup.link_to_parent(collections, export_collection)
    return feedback


def get_combination_name(objects: List[bpy.types.Object]) -> str:
    """Create a unqique name based on objects' names.

    :param objects: Objects that form a combination.
    :type objects: List[bpy.types.Object]
    :return: Unique name for the given combination of objects.
    :rtype: str
    """
    if not objects:
        return ""
    # Set a name for the new collection. All objects have the same armature, get its type from the first.
    comp_string = " ".join(sorted([obj.name for obj in objects]))
    suffix = hashlib.blake2s(comp_string.encode(), digest_size=8).hexdigest()  # 16 characters.
    skeleton = fops.get_skeleton_type(objects[0].name)
    return "-".join(("set", skeleton, suffix))


def export_combinations(context, export_path: Union[Path, str]) -> List[tuple]:
    """Export combinations to GLB files.

    :param context: Blender's context.
    :type context: bpy.types.Context
    :param export_path: Target folder for batch-exporting combinations to GLB files.
    :type export_path: Union[Path, str]
    :return: Error messages.
    :rtype: List[tuple]
    """
    feedback = []
    try:
        export_collections = context.scene.collection_map[str(CollNames.EXPORT)].collection.children
    except (AttributeError, KeyError):
        feedback.append(Feedback(type='ERROR', msg="Scene is not initialized properly. Missing export collection."))
        return feedback

    for collection in export_collections:
        try:
            file_path = write_collection(collection, export_path)
        except IOError as e:
            # Warn, an error would abort all other files as well.
            feedback.append(Feedback(type='WARNING', msg=f"Failed to export combination {collection.name}.\n{str(e)}"))
            continue
        feedback.append(Feedback(type='INFO', msg=f"Exported combination to {file_path}."))

    objops.deselect_all()
    context.view_layer.objects.active = None
    return feedback


def write_collection(collection: bpy.types.Collection, path: Union[Path, str]) -> str:
    """Export the objects in a collection to file.

    :param collection: Collection to export. Its name will serve as the filename if the export path points to a folder.
    :type collection: bpy.types.Collection
    :param path: Where to save the file. If a directory is given, the file-name will be the collection's name.
    :type path: Union[Path, str]
    :return: File path to exported collection. Empty on failure.
    :rtype: str
    """
    # Export is based on object selections and visibility.
    objops.show_select_objects(collection.all_objects)
    path = fops.get_abs_path(path)
    if path.is_dir():
        path = str((path / collection.name.replace(".", "_")).with_suffix('.glb'))
    try:
        ret = bpy.ops.export_scene.gltf(filepath=path, use_selection=True, check_existing=False)
    except IOError:
        ret = {'CANCELLED'}
        raise
    return path if ret != {'CANCELLED'} else ""
