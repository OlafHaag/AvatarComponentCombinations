# Plan of Execution for the Assignment

## Goals

Consider S.T.A.R. method: Situation, Task, Action, Result
If the result satisfies the tasks by the actions taken has to be evaluated afterwards.

### Situation

Avatars have clothing.
The clothing is customizable.
The customization includes choosing the top, bottom, and footwear.
These parts are saved in different files with a standard skeleton definition.
In the future, more clothing parts could be introduced (e.g. gloves), and clothing parts could come with LODs.
Files could also contain animation.

Combinations of the clothing pieces are needed to form an arbitrary number of unique full body outfits.
Each full body outfit shall be saved individually.

With an increasing number of clothing pieces and full-body outfits needed, a manual approach doesn't scale well.
This may become a bottleneck in production.
Furthermore, having artists do this repetitive task manually may be detrimental to their motivation and costs the company valuable resources that are better spent on creative tasks.

### Task

- Free up the time of artists by reducing the effort to produce many full-body outfits.
- Reduce potential for human error.
- Make the process as frictionless as possible and in best-case even enjoyable.

### Action

#### Primary Action

- > **Create a tool** that can be used to generate new full-body outfits by combining the existing pieces of clothing.
- Use Blender, since this is the preferred DCC used by the artists. And it's free, which makes it easier for me.
- Create the tool as an add-on. This makes it easy to install and operate in Blender.
- Create a minimal working example, so the core task is fulfilled.
  - That means a one-off command-line interface. This also facilitates the separation of concerns, that is, separate the core logic from the UI.
  - Concentrate on current situation and what's needed **now**. Leave future-proof considerations for later, shall the need arise.
  - It also means not implementing every possible safety/sanity-check and corner-case right away.
- Choose GLB as the export format, because Blender's FBX exporter can't embed textures.
  - On the downside this means that full-body assets don't share textures and overall more memory is used.
  - On the upside this makes sharing individual assets way easier.
  - Also, individual outfit's textures could be customized even further without affecting other outfits.

#### Secondary Action

- > Using the included textures, create 2-3 texture variations of the outfits.

#### Tertiary Action

- Provide artists with the resources to be flexible, if they need it.
  - Give control over import/export paths, number of full-body outfits, naming conventions.
  - Provide GUI, since these are more artist-friendly.

## Checklists

The following tasks begin with a priority assignment, ranging from the highest priority (1) to the lowest priority (4).
All priority 1 tasks must be met. They are necessary for creating a minimal working example.
Priority 2 tasks enable a better experience, or more flexibility, e.g. by providing a GUI.
Tasks of priority 3 are a bonus requirement by the assignment.
Priority 4 tasks are, for example, optional enhancements that are not specifically mentioned by the assignment. These tasks will probably not be implemented and will be re-evaluated at a later development stage.

### Get Up and Running

- [x] 1 - Get assignment + files.
- [x] 4 - Look for an already existing solution to save cost.
  - This is usually prio 1, but this assignment is about my own handiwork, I guess.
  - A quick search offered no ready-made solution.
- [x] 1 - Get Blender.
  - Decided on latest stable (non-LTS) 2.92.0.
- [x] 2 - Init repo.
- [x] 1 - Review files (look before you leap).
  - **_outfit-f-top-cyberpunk-04-v2.fbx_ does not conform to input naming convention. Assumed to be human error. Should be _outfit-f-cyberpunk-04-v2-top.fbx_**
  - [ ] 4 - Check consistent bone names between files, and Mixamo compatibility.
- [x] 2 - Complete writing this plan.
- [x] 1 - Prioritize tasks.
- [x] 2 - Setup VSCode for Blender add-on development.
  - [x] 2 - Python 3.7.7 environment to match Blender 2.92.
  - [x] 3 - Setup linting, autocompletion.
    - looked at most recent efforts for autocompletion in build-process, not ready yet.
    - decided on [fake-bpy-module](https://github.com/nutti/fake-bpy-module).

### Implementation

#### Modules

Having specialized modules helps with reusability of code segments. But it's not strictly necessary for a prototype.

- [x] 1 - Init. Import modules, register add-on.
- [ ] 2 - IO modules. Contain batch import and export functions.
- [x] 2 - Main logic. Like changing armature, sorting, combinations of models and their texture assignments.
- [x] 3 - GUI module. Displays buttons, text fields etc.
- [ ] 4 - Tests. Makes sure everything works as expected, especially after changes and software updates.

#### Steps

- [x] 2 - Create new scene to not mess with any opened scene and its content.
  - [ ] 4 - Give the option to import into current scene.
- [x] 1 - Read files with assumed folder-structure: <part category>/<part>/<part>.fbx
  - [x] 1 - For the body parts the structure is: <part category>/<part>.fbx
  - Handled by just ignoring subfolders that are not a category (second level).
- [x] 1 - Import multiple files onto single skeleton.
  - Blender does not support importing onto an existing skeleton. Have to reassign target armature in modifier, re-parent, and delete additional armature.
  - [x] 1 - Handle consistency of object/mesh names.
  - [x] 1 - Handle consistency of material names.
  - [x] 1 - Handle consistency of armature names.
- [x] 1 - Have a source- and an export-collection.
- [x] 2 - Sort component meshes (top, bottom, footwear, and body) into respective category source-collections.
  - [x] 1 - Have a collection with mandatory components that will be in each export collection, e.g. the armature.
  - [x] 3 - Having a “failed”-collection, e.g. when naming pattern isn't recognized, no skeleton, (or skeleton hierarchy differs).
- [x] 1 - Recombine mesh components from each part category and link the combination to a unique export sub-collection.
  - [x] 1 - Allow each combination only once. Easiest: Create all possible combinations (Cartesian product) and choose an arbitrary number (10) for which to create export-collections. Doesn't scale well, probably only good for small amount of parts, but good enough for now.
  - [ ] 3 - Mind texture variations, too. Do this on the import step.
  - [x] 1 - Choose a naming convention for export collection, which will form the file name.
    - Include skeleton type in name, since this is the only denominator between components.
    - Writing each component into the name quickly becomes unfeasible.
    - UUIDs would always create new files, although combinations might already exist.
    - Adding a hash value based on included components on export may not be very human-readable, but would solve the above and could be “reverse-engineered” if all possible component combinations are known (which we do).
  - Enables easier review of full-body-outfits by artists.
  - Enables flexibility and creation of custom, intentional combinations, e.g. whole sets.
  - Collections define naming convention for exported files. Enables custom naming by artists.
- [ ] 4 - Maybe — optionally — create a view layer for each export sub-collection, in case renders of all the outfits are needed.
- [x] 1 - Save each export-collection to GLB.
- [ ] 4 - Operator to clear export collections.
- [ ] 4 - Write unit tests (low prio for a rapid prototype, otherwise higher).
- [ ] 4 - Automatic testing of add-on in different Blender versions.

### Documentation

- [ ] 1 - Installation
- [ ] 1 - Usage
  - [ ] 2 - Ctrl+click on view layer's eye symbol to isolate a full-body-outfit for review.
  - [ ] 2 - Hold ctrl when linking assets to export collection manually by dragging assets from source collection to export collection. Do not use "move".
- [ ] 2 - Naming conventions
- [ ] 4 - Video instructions

## Take-away

- **If the amount of avatar components became quite large, it would take way too much time to import all of them into Blender just to recombine a randomly selected handful of them. In that case the selection and recombination should happen on the file-path level and only those files should be imported that are actually needed.**
- Avoid using operators in loops. Most operators update the scene, because they are intended to be invoked by the user interface. Hence, the scene updating slows down the Python script.
- Blender's FBX support is rudimentary and the documentation is abysmal.
- If an FBX with a skeleton is imported from another DCC software to Blender, Blender adds the Armature as root. Upon exporting back to FBX, the skeleton hierarchy changes. This is terrible!
