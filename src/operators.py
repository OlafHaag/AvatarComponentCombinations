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

from .scenemanager import (batch_import_components,
                           add_combinations_to_export,
                           export_combinations,
                           )


class ImportAvatarComponents(bpy.types.Operator):
    """Import avatar components from given parent folder path"""

    bl_idname = "import_scene.import_avatar_components"
    bl_label = "Import avatar components from FBX files."
    bl_options = {'UNDO'}

    import_path: bpy.props.StringProperty(
        name="Import Folder",
        description="Root import folder for batch-importing FBX files with avatar components.",
        subtype='DIR_PATH',
        default="//",
    )
    use_texture_variants: bpy.props.BoolProperty(
        name="Import Texture Variants",
        description="Import other texture variants of components.",
        default=False,
    )

    def execute(self, context):
        feedback = batch_import_components(context,
                                           self.import_path,
                                           use_new_scene=True,
                                           use_variants=self.use_texture_variants)
        for msg_type, msg in feedback:
            self.report({msg_type}, msg)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.import_path = context.scene.import_root_path
        self.use_texture_variants = context.scene.use_import_texture_variants
        return self.execute(context)


class CombineAvatarComponents(bpy.types.Operator):
    """Combine avatar components to form full arrangements"""

    bl_idname = "acc.combine_avatar_components"
    bl_label = "Combine avatar components."
    bl_options = {'REGISTER', 'UNDO'}

    n_combinations: bpy.props.IntProperty(
        name="Combinations",
        description="Number of combinations to create from components.",
        default=10,
        min=1,
        soft_max=10,
    )
    use_only_matching_sets: bpy.props.BoolProperty(
        name="Only Whole Sets",
        description="Combine only components with the same texture variants.",
        default=False,
    )

    def execute(self, context):
        feedback = add_combinations_to_export(context.scene, self.n_combinations)
        for msg_type, msg in feedback:
            self.report({msg_type}, msg)
            if msg_type == 'ERROR':
                return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        # When called via UI. ask user how many combinations should be made.
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class ExportAvatarCombinations(bpy.types.Operator):
    """Export combinations of avatar components to GLB format"""

    bl_idname = "export_scene.export_avatar_combinations"
    bl_label = "Export avatar combinations."

    export_path: bpy.props.StringProperty(
        name="Export Folder",
        description="Target folder for batch-exporting GLB files with full-body outfits.",
        subtype='DIR_PATH',
        default="//",
    )

    def execute(self, context):
        # Is glTF2 add-on activated?
        if not hasattr(bpy.types, bpy.ops.export_scene.gltf.idname()):
            self.report({'ERROR'}, "glTF2 Import-Export Add-on needs to be activated.")
            return {'CANCELLED'}

        feedback = export_combinations(context, self.export_path)
        for msg_type, msg in feedback:
            self.report({msg_type}, msg)
            if msg_type == 'ERROR':
                return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        self.export_path = context.scene.export_path
        return self.execute(context)


class AutoImportExportAvatars(bpy.types.Operator):
    """Import avatar components and export combinations in one go without user interaction"""

    bl_idname = "acc.auto_export_avatars"
    bl_label = "Import FBX components and export GLB full-body avatars."
    bl_options = {'UNDO'}

    import_path: bpy.props.StringProperty(
        name="Import Folder",
        description="Root import folder for batch-importing FBX files with avatar components.",
        subtype='DIR_PATH',
        default="//",
    )
    export_path: bpy.props.StringProperty(
        name="Export Folder",
        description="Target folder for batch-exporting GLB files with fullbody outfits.",
        subtype='DIR_PATH',
        default="//",
    )
    n_combinations: bpy.props.IntProperty(
        name="Combinations",
        description="Number of combinations to create from components.",
        default=10,
        min=1,
        soft_max=10,
    )
    use_texture_variants: bpy.props.BoolProperty(
        name="Import Texture Variants",
        description="Import other texture variants of components.",
        default=False,
    )
    use_only_matching_sets: bpy.props.BoolProperty(
        name="Only Whole Sets",
        description="Combine only components with the same texture variants.",
        default=False,
    )

    def execute(self, context):
        # Check Import-Export add-on availability before we take any action.
        # Is glTF2 add-on activated?
        if not hasattr(bpy.types, bpy.ops.export_scene.gltf.idname()):
            self.report({'ERROR'}, "glTF2 Import-Export Add-on needs to be activated.")
            return {'CANCELLED'}

        try:
            # Import.
            feedback = batch_import_components(context, self.import_path, use_new_scene=True)
            for msg_type, msg in feedback:
                self.report({msg_type}, msg)
                if msg_type == 'ERROR':
                    return {'CANCELLED'}

            # Combine components.
            feedback = add_combinations_to_export(context.scene, self.n_combinations)
            for msg_type, msg in feedback:
                self.report({msg_type}, msg)
                if msg_type == 'ERROR':
                    return {'CANCELLED'}

            # Export.
            feedback = export_combinations(context, self.export_path)
            for msg_type, msg in feedback:
                self.report({msg_type}, msg)
                if msg_type == 'ERROR':
                    return {'CANCELLED'}

        except RuntimeError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        self.import_path = context.scene.import_root_path
        self.export_path = context.scene.export_path
        self.n_combinations = context.scene.n_component_combinations
        self.use_texture_variants = context.scene.use_import_texture_variants
        self.use_only_matching_sets = context.scene.use_only_matching_sets
        return self.execute(context)
