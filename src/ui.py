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


class VIEW3D_PT_AvatarComponentCombinations(bpy.types.Panel):
    """Add-on panel for options and calling the operator."""

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Avatar"
    bl_label = "Component Combinations"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        # Paths.
        col.prop(context.scene, "import_root_path")
        col.prop(context.scene, "export_path")
        # Main buttons.
        col = layout.column(align=True)
        # Import button.
        prop = col.operator("import_scene.import_avatar_components",
                            text="Import",
                            icon='IMPORT')
        prop.import_path = context.scene.import_root_path
        # Combine button.
        prop = col.operator("acc.combine_avatar_components",
                            text="Combine",
                            icon='SELECT_EXTEND')
        prop.n_combinations = context.scene.n_component_combinations
        # Import button.
        prop = col.operator("export_scene.export_avatar_combinations",
                            text="Export",
                            icon='EXPORT')
        prop.export_path = context.scene.export_path
        # Settings.
        layout.separator()
        layout.label(text="Settings:")
        col = layout.column(align=True)
        col.enabled = False
        col.prop(context.scene, "use_import_texture_variants")
        col.prop(context.scene, "use_only_matching_sets")
        layout.prop(context.scene, "n_component_combinations")
        # Auto execution.
        layout.separator()
        layout.label(text="All-in-One:")
        # Auto import+export button.
        prop_import_export = layout.operator("acc.auto_export_avatars",
                                             text="Import+Export",
                                             icon='UV_SYNC_SELECT')
        prop_import_export.import_path = context.scene.import_root_path
        prop_import_export.export_path = context.scene.export_path
        prop_import_export.n_combinations = context.scene.n_component_combinations
