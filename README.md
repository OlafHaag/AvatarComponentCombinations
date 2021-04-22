# Avatar Component Combinations

This [Blender](https://www.blender.org) add-on allows you to batch-import rigged body-part assets from FBX files, recombine them to form full-body sets sharing the same armature, and then batch-export the sets to glTF binary format.
It can execute the whole process automatically, or allow artists to be flexible by going through these steps one-by-one.

## Installation

- Download the **[Latest Add-on Release](https://github.com/OlafHaag/AvatarComponentCombinations/releases/latest/AvatarComponentCombinations.zip)**.
  Or go to the [Release page](https://github.com/OlafHaag/AvatarComponentCombinations/releases) of this repository and download the **AvatarComponentCombinations.zip** file from a release. It's under the “Assets” triangle menu, if you don't see it right away.
  - ***Note:*** Downloading just the source code from the repository won't work!
- Start Blender, open its _Preferences_, and choose _Add-ons_ in the left sidebar.
- To install the add-on, use the _Install…_ button in the top row and use the File Browser to select the **AvatarComponentCombinations.zip** add-on file you just downloaded.
- Now the add-on will be installed, however not automatically enabled.
  The search field will be set to the add-on’s name (to avoid having to look for it), Enable the add-on by checking the enable checkbox.
- Make sure the _FBX format_ and _glTF 2.0 format_ add-ons that come with Blender are enabled as well.
  This is the default.
  The add-on will warn you, if they are disabled.

## Usage

You can use the add-on via Blender's user-interface or use the command-line to run the operator's python command.

### Using the Blender Interface

Watch the video below to see how the add-on is installed and used through Blender's GUI.
[![Demonstration of Avatar Component Combinations](http://img.youtube.com/vi/TODO/0.jpg)](http://www.youtube.com/watch?v=TODO "Demonstration of Avatar Component Combinations")

### Command-line

If you don't need to intervene in the process of preparing and drawing random asset combinations, and you just want to get a random selection of combinations quickly, you can run the _auto\_export\_avatars_ operator from the command-line.

```python
blender --background --python-expr "import bpy;bpy.ops.acc.auto_export_avatars(import_path='path/to/components_root', export_path='path/to/export_folder/', n_combinations=10)"
```

If you're on Windows, you can either use the forward-slash path separator (`/`), or you must use the double back-slash path separator (`\\`).

#### Parameters

- import_path: Root import folder for batch-importing FBX files with avatar components.
- export_path: Target folder for batch-exporting GLB files with full-body outfits.
- n_combinations: Number of full-body outfits to export. Optional. Default is 10.
- [PLANNED] use_import_texture_variants: Import other texture variants of components.
- [PLANNED] use_only_whole_sets: Combine only components with the same texture variants.

## Conventions
 
In order for the add-on to work properly, your input files need to be in a specific folder structure and have specific names.

### Folder structure

### Naming
