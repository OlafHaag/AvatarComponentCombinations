# Avatar Component Combinations

## Installation

- Make sure the FBX and GLTF add-ons that come with Blender are activated as well. This is the default.

## Usage

### Command-line
`blender --python-expr "import bpy;bpy.ops.acc.auto_export_avatars(import_path='path/to/components_root', export_path='path/to/export_folder/', n_combinations=20)"`
If you're on Windows, you can either use the forward-slash path separator (`/`), or you must use the double back-slash path separator (`\\`).

#### Parameters

- import_path: Root import folder for batch-importing FBX files with avatar components.
- export_path: Target folder for batch-exporting GLB files with full-body outfits.
- n_combinations: Number of full-body outfits to export. Optional. Default is 10.

### Blender Interface

## Conventions

### Folder structure

### Naming
