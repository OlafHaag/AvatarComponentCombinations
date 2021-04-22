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

import bpy
from . import auto_load

bl_info = {
    "name": "Avatar Component Combinations",
    "author": "Olaf Haag <contact@olafhaag.com>",
    "description": "Batch import of avatar components, and export of full-body combinations.",
    "blender": (2, 92, 0),
    "version": (0, 0, 1),
    "location": "3D View > Sidebar > Avatar",
    "warning": "",
    "doc_url": "https://github.com/OlafHaag/AvatarComponentCombinations/blob/main/README.md",
    "tracker_url": "https://github.com/OlafHaag/AvatarComponentCombinations/issues",
    "category": "Import-Export"
}


class ImportFilePath(bpy.types.PropertyGroup):
    """Property that saves a file-path for a file that shall be imported."""

    path: bpy.props.StringProperty(
        name="File",
        description="File to import into the scene.",
        subtype='FILE_PATH',
    )
    category: bpy.props.StringProperty(
        name="Category",
        description="Component category this file belongs to.",
        default="_failed",
    )


class CollectionMap(bpy.types.PropertyGroup):
    """Map the intended name for collections to their references."""

    name: bpy.props.StringProperty(
        name="Name",
        description="Intended name for the collection without a counter-suffix.",
    )
    collection: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="Pointer to collection.",
    )


def declare_addon_properties():
    """Declare properties used by the add-on."""
    bpy.types.Scene.import_root_path = bpy.props.StringProperty(  # We can use different scenes for separate imports.
        name="Import Folder",
        description="Root import folder for batch-importing FBX files with avatar components",
        subtype='DIR_PATH',  # Blender's style guide uses single quotes to mark enumerations.
        default="//",
    )
    bpy.types.Scene.export_path = bpy.props.StringProperty(
        name="Export Folder",
        description="Export folder for batch-exporting GLB files with avatar component combinations",
        subtype='DIR_PATH',
        default="//",
    )
    bpy.types.Scene.import_files = bpy.props.CollectionProperty(type=ImportFilePath)
    bpy.types.Scene.collection_map = bpy.props.CollectionProperty(type=CollectionMap)
    bpy.types.Scene.n_component_combinations = bpy.props.IntProperty(
        name="Combinations",
        description="Number of combinations to create from components",
        default=10,
        min=1,
        soft_max=10,
    )
    bpy.types.Object.src_file = bpy.props.StringProperty(
        name="Source File",
        description="Source file path from which the asset was imported",
        subtype='FILE_PATH',
    )
    bpy.types.Scene.use_only_whole_sets = bpy.props.BoolProperty(
        name="Only Whole Sets",
        description="Combine only components with the same texture variants.",
        default=False,
    )
    bpy.types.Scene.use_import_texture_variants = bpy.props.BoolProperty(
        name="Import Texture Variants",
        description="Import other texture variants of components.",
        default=False,
    )


def remove_addon_properties():
    """Remove the custom add-on properties."""
    del bpy.types.Scene.import_root_path
    del bpy.types.Scene.export_path
    del bpy.types.Scene.import_files
    del bpy.types.Scene.collection_map
    del bpy.types.Scene.n_component_combinations
    del bpy.types.Object.src_file
    del bpy.types.Scene.use_only_whole_sets
    del bpy.types.Scene.use_import_texture_variants


auto_load.init()


def register():
    # Find all classes to register.
    auto_load.register()
    # Elements of CollectionProperty have to be registered manually before property declarations who use them.
    bpy.utils.register_class(ImportFilePath)
    bpy.utils.register_class(CollectionMap)
    declare_addon_properties()


def unregister():
    remove_addon_properties()
    bpy.utils.unregister_class(CollectionMap)
    bpy.utils.unregister_class(ImportFilePath)
    # Find all classes to unregister.
    auto_load.unregister()
