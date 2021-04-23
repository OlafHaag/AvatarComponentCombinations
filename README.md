# Avatar Component Combinations

This [Blender](https://www.blender.org) add-on allows you to batch-import rigged body-part assets (avatar components) from FBX-files, recombine them to form full-body sets sharing the same armature, and then batch-export the sets to glTF binary format.
It can execute the whole process automatically, or allow artists to be flexible by going through these steps one-by-one.

## Installation

- Download the **[Latest Add-on Release](https://github.com/OlafHaag/AvatarComponentCombinations/releases/latest/download/AvatarComponentCombinations.zip)**.
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

You can use the add-on via Blender's user-interface or use the command-line to run the add-on's operator with a python command.

### Using the Blender Interface

Watch the video below to see how the add-on is installed and used through Blender's GUI.
[![Demonstration of Avatar Component Combinations](https://img.youtube.com/vi/rvdBwaWIY7k/0.jpg)](https://youtu.be/rvdBwaWIY7k "Demonstration of Avatar Component Combinations")

### Command-line

If you don't need to intervene in the process of preparing and drawing random asset combinations, and you just want to get a random selection of combinations quickly, you can run the _auto\_export\_avatars_ operator from the command-line.

```cmd
blender --background --addons AvatarComponentCombinations --python-expr "import bpy;bpy.ops.acc.auto_export_avatars(import_path='path_to/components_root', export_path='path_to/export_folder/', n_combinations=10)"
```

If you're on Windows, you can either use the forward-slash path separator (`/`), or you must use the double back-slash path separator (`\\`).

#### Parameters

- import_path: Root import folder for batch-importing FBX files with avatar components.
- export_path: Target folder for batch-exporting GLB files with full-body outfits.
- n_combinations: Number of full-body outfits to export. Optional. Default is 10.
- [PLANNED] use_import_texture_variants: Import other texture variants of components.
- [PLANNED] use_only_whole_sets: Combine only components with the same texture variants.

## Conventions

In order for the add-on to work properly, your input files need to be in a specific folder structure and follow a naming convention.

### Folder structure

The FBX-files containing individual avatar components must first be grouped by the skeleton type they share, an armature hierarchy for either a male or a female avatar, for example.
The folder path you set to import from must then only contain subfolders for each body-region category as immediate children.
The body-region categories must not contain dashes (“-”).
The body-region folders can have more levels of subfolders for organizational purposes, but it's not necessary.
The naming of these organizational subfolders doesn't matter.

If the texture maps are not embedded in the FBX-file, they should be placed next to the FBX-file they belong to. At least all texture maps belonging to an individual asset should be together in the same folder.

Example:

```txt
Import Path Female Avatar Components/
|
|___body/
|   |___skin-f-generic-01-v1-body.fbx
|   |___skin-f-generic-02-v1-body.fbx
|   |___skin-f-generic-01-v1-body-D.jpg
|   |___skin-f-generic-01-v1-body-N.jpg
|   |___skin-f-generic-02-v1-body-D.jpg
|   |___skin-f-generic-02-v1-body-N.jpg
|
|___bottom/
|   |___outfit-f-casual/
|   |   |___outfit-f-casual-01-v2-bottom.fbx
|   |   |___outfit-f-casual-02-v2-bottom.fbx
|   |   |___outfit-f-casual-01-v2-bottom-D.jpg
|   |   |___outfit-f-casual-01-v2-bottom-N.jpg
|   |   |___outfit-f-casual-01-v2-bottom-R.jpg
|   |   |___outfit-f-casual-02-v2-bottom-D.jpg
|   |   |___outfit-f-casual-02-v2-bottom-N.jpg
|   |   |___outfit-f-casual-02-v2-bottom-R.jpg
|   |
|   |___outfit-f-office-05/
|   |   |___outfit-f-office-05-v1-bottom.fbx
|   |   |___outfit-f-office-05-v1-bottom-D.jpg
|   |   |___outfit-f-office-05-v1-bottom-N.jpg
|   |   |___...
|   ...
|
|___footwear/
|   |___...
|   |   |___...
|   |
|   |___...
|
|___top/
    |___...
```

### Naming Conventions

#### Input files

- The body-region categories must not contain dashes (“-”).
- The naming or depth of organizational subfolders within body-region directories doesn't matter. (Absolute paths should not exceed 256 characters, though.)
- FBX files should follow this naming pattern: `<type>-<skeleton>-<theme>-<variant>-<mesh>-<region>.fbx`, e.g. _../body/skin-f-generic-02-v1-body.fbx_. **Note** how the region tag is the same as the body-region folder's name.
  - If tags are missing towards the end of the filename, they'll be set to default values for the objects in the Blender scene:
`undefined-x-generic-01-v1-undefined`.
- Texture maps should follow this similar naming pattern: `<type>-<skeleton>-<theme>-<variant>-<mesh>-<region>-<map>.ext`, e.g. _../bottom/somefolder/outfit-f-office-05-v1-bottom-N.jpg_

#### Output files

- Exported files are named after the collection that was exported. The default is `set-<skeleton>-<hash>.glb`, e.g. _set-f-3e7dab4e03c0ee83.glb_.
  - The _skeleton_ tag designates the type of skeleton, that is shared among the contained components.
  - The _hash_ tag is based on the avatar component names within this set. Sets containging the exact same components would yield the same file-name.
- The exported GLB files have their texture maps embedded. This makes sharing individual sets easier.
- The armature object name in each set has a suffix that designates its type, e.g. `Armature-f`. This is the _skeleton_ tag all contained components must have in common.
