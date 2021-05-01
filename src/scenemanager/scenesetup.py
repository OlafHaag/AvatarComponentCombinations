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
from typing import (Optional,
                    Union,
                    Dict,
                    Iterable,
                    List,
                    )
import bpy

from . import objects as objops
from .. import file_ops as fops
from .. import CollNames


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


def link_to_parent(children: Union[bpy.types.Collection, Iterable[bpy.types.Collection]], parent: bpy.types.Collection):
    """Link collection or collections to a parent collection.

    :param children: Collection(s) to be  linked to parent collection.
    :type children: Union[bpy.types.Collection, Iterable[bpy.types.Collection]]
    :param parent: Parent collection.
    :type parent: bpy.types.Collection
    """
    if not isinstance(children, Iterable):
        children = [children]
    for child in children:
        parent.children.link(child)


def create_initial_collections(scene: Optional[bpy.types.Scene] = None) -> Dict[str, bpy.types.Collection]:
    """Create source and export collections, as well as failed, ignore, and mandatory subcollections in source.

    :param scene: Scene in which to create new collections.
    :return: Mapping of names to references for new collections.
    :rtype: Dict[str, bpy.types.Collection]
    """
    if not scene:
        scene = bpy.context.scene
    # Create new collections.
    collections = create_collections([CollNames.SOURCE, CollNames.EXPORT], parent=scene.collection)
    collections.update(create_collections([CollNames.FAILED, CollNames.IGNORE, CollNames.MANDATORY],
                                          parent=collections[CollNames.SOURCE]))

    collections[CollNames.SOURCE].hide_render = True
    collections[CollNames.IGNORE].hide_viewport = True
    # Color them for easy identification.
    collections[CollNames.SOURCE].color_tag = 'COLOR_05'  # Blue.
    collections[CollNames.FAILED].color_tag = 'COLOR_01'  # Give red warning color.
    collections[CollNames.IGNORE].color_tag = 'COLOR_02'  # Orange.
    collections[CollNames.MANDATORY].color_tag = 'COLOR_03'  # Yellow.
    collections[CollNames.EXPORT].color_tag = 'COLOR_04'  # Greenlit for export.
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
    collections = {n: bpy.data.collections.new(str(n)) for n in names}
    # If not linked to a parent, new collections will only live in Blender’s internal data.
    if parent:
        link_to_parent(collections.values(), parent)
    return collections


def objects_to_collection(objects: List[bpy.types.Object], name: str) -> bpy.types.Collection:
    """Create a collection and link objects to it.

    If the list of objects is empty, the collection will be created anyway.
    The new collection exists in Blender's internal data and is not yet linked to a parent collection.

    :param objects: Objects to be linked to a new collection.
    :type objects: List[bpy.types.Object]
    :return: Reference to new collection.
    :rtype: Optional[bpy.types.Collection]
    """
    collection = bpy.data.collections.new(name)
    # Link object to collection.
    for obj in objects:
        collection.objects.link(obj)
    return collection


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
            col_map.name = str(key)
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
        root_path = fops.get_abs_path(scene.import_root_path)
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
    if not fops.get_abs_path(import_path).is_dir():
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
    cat_collections = create_collections(categories, parent=init_collections[CollNames.SOURCE])
    if not set_collection_map_as_property(scene, cat_collections):  # No category collections?
        return False
    if not set_importfiles_props(scene):  # Scene not initialized or no files found?
        return False

    return True
