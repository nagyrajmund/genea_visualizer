import bpy 
import sys, os, time, importlib, re, tempfile
from os.path import join
from pathlib import Path as myPath
from mathutils import Vector
import numpy as np
# sys.stdout = open("C://Users//tmh//Desktop//Rajmund//genea_visualizer-dev-2025//genea_visualizer-dev-2025//output.txt", 'w')
print('test')

import sys
import subprocess
import os
# To install pandas, open Blender as admin, go to scripting, and run import pip, then pip.main(["install", "pandas"]) in the REPL environment
import pandas as pd 

class SequentialRenderOperator(bpy.types.Operator):
    bl_idname = "render.sequential_animations"
    bl_label = "Render Animations Sequentially"
    
    render_queue = []
    is_rendering = False
    
    def execute(self, context):
        # Define the animations (scenes or cameras to render)
        self.render_queue = self.setup_queue()
        
        # self.render_queue = [
        #     {"filepath": "//output/animation1_", "start": 1, "end": 100},
        #     {"filepath": "//output/animation2_", "start": 101, "end": 200},
        # ]
        
        # Start the modal handler
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
    
    def modal(self, context, event):
        if not self.is_rendering:
            if self.render_queue:
                
                clear_character()
                
                render_settings = self.render_queue.pop(0)
                SMPLX_FILENAME_IN = render_settings["filepath"]
                main() # Should have the take path as parameter for main(SMPLX_FILENAME_IN)
                
                # Start rendering
                self.is_rendering = True
                bpy.ops.render.render('EXEC_DEFAULT', animation=True)
            else:
                # No more renders left, finish operator
                return {"FINISHED"}
        
        # Check if rendering is done
        if not bpy.app.is_job_running("RENDER"):
            self.is_rendering = False  # Ready for next render

        return {"RUNNING_MODAL"}
    
    def setup_queue(self):
        render_queue = []
        
        IN_SCRIPT_DIR = myPath(bpy.context.space_data.text.filepath).parents[0]
        in_file_path = 'S://Work//GENEA//GENEA2024//beat_v2.0.0//beat_english_v2.0.0//train_test_split.csv'
        IN_ARG_OUTPUT_DIR = IN_SCRIPT_DIR / 'output/Leaderboard/SMPLX/Updated'
        
        matches = load_data.filter_csv_by_type(in_file_path)

        i = 0
        for File in matches:
            if (i == 85): # was 87
                print(File)
                render_queue.append({
                    "filepath": File,
                })
                
            if (i == 126):
                print(File)
                render_queue.append({
                    "filepath": File,
                })
            
            i += 1
            
        return render_queue

from bpy.app.handlers import persistent

@persistent
def load_handler(dummy):
    print("Load Handler:", bpy.data.filepath)

bpy.app.handlers.load_post.append(load_handler)

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]
sys.path.append(os.path.join(script_dir, "scripts"))

import load_data
importlib.reload(load_data)
import create_scene
importlib.reload(create_scene)
import create_camera
importlib.reload(create_camera)
import create_material
importlib.reload(create_material)
import edit_character
importlib.reload(edit_character)
import edit_audio
importlib.reload(edit_audio)
import parser
importlib.reload(parser)
    
def setup_char_clothes(char):
    mesh = char.children[0]
    mat = mesh.material_slots[0].material
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    bsdf_node = mat.node_tree.nodes["Principled BSDF"]
    material_output = mat.node_tree.nodes["Material Output"]
    
    for node in nodes:
        if node.type == 'TEX_IMAGE':
            texture_diffuse = node
    
    texture_displacement = nodes.new(type='ShaderNodeTexImage')
    multiply_node = nodes.new(type='ShaderNodeVectorMath')
    multiply_node.operation = 'MULTIPLY'
    scale_node = nodes.new(type='ShaderNodeVectorMath')
    scale_node.operation = 'SCALE'
    attribute_node = nodes.new(type='ShaderNodeAttribute')
    value_node = nodes.new(type='ShaderNodeValue')
    divide_node = nodes.new(type='ShaderNodeMath')
    divide_node.operation = 'DIVIDE'

    # Position the nodes
    texture_diffuse.location      = (-600, 200)
    texture_displacement.location = (-600, -100)
    attribute_node.location       = (-600, -400)
    value_node.location           = (-400, -500)
    bsdf_node.location                 = (-200, 200)
    multiply_node.location        = (-200, -200)
    divide_node.location          = (-200, -400)
    scale_node.location           = (0, -200)
    material_output.location            = (200, -200)
    
    try:
        diffuse_filepath = texture_diffuse.image.filepath
        if "smplx_texture_f_alb.png" in diffuse_filepath:
            texture_filename = "smplx_texture_f_disp.png"
        elif "smplx_texture_m_alb.png" in diffuse_filepath:
            texture_filename = "smplx_texture_m_disp.png"
        else:
            print(f"Could not determine displacement texture from filepath: {diffuse_filepath}")
            return

        if texture_filename not in bpy.data.images:
            print(os.path.realpath(__file__))
            addon_path = os.path.dirname(os.path.realpath(__file__))
            texture_path = os.path.join(addon_path, "data", texture_filename)
            texture_displacement.image = bpy.data.images.load(texture_path)
        else:
            texture_displacement.image = bpy.data.images[texture_filename]

    except RuntimeError:
        print(f"Failed to load texture: {texture_path}")
        return

    attribute_node.attribute_name = "norm"
    value_node.outputs['Value'].default_value = 10
    divide_node.inputs[1].default_value = 1000

    # Create connections
    links.new(texture_diffuse.outputs['Color'], bsdf_node.inputs['Base Color'])
    links.new(bsdf_node.outputs['BSDF'], material_output.inputs['Surface'])
    links.new(texture_displacement.outputs['Color'], multiply_node.inputs[0])
    links.new(attribute_node.outputs['Vector'], multiply_node.inputs[1])
    links.new(multiply_node.outputs['Vector'], scale_node.inputs['Vector'])
    links.new(value_node.outputs['Value'], divide_node.inputs[0])
    links.new(divide_node.outputs['Value'], scale_node.inputs['Scale'])
    links.new(scale_node.outputs['Vector'], material_output.inputs['Displacement'])
    
def _set_frame_and_reposition_camera(scene, start_frame):
    """ 
    Update the animation data of the character to `start_frame`, 
    and reposition the camera so that the character is still in focus.
    """
    # STEP 1: store character's original location
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            smplx_char = obj
            break
    pelvis_bone = smplx_char.pose.bones['pelvis']
    old_pelvis_location = Vector(pelvis_bone.location)
    
    # STEP 2: update the character's location 
    scene.frame_start = start_frame
    scene.frame_set(start_frame)
    new_pelvis_location = Vector(pelvis_bone.location)
    
    # STEP 3: compute the displacement between the two locations
    # (Rajmund) NOTE: I think the pelvis bone and the camera have different axis convention.
    #                 Switching the coordinates as below (camera.Z becomes bone.Y, and camera.Y becomes -bone.Z) works.
    camera_transl = Vector((
        # X
        new_pelvis_location[0] - old_pelvis_location[0],
        # -Y
        -(new_pelvis_location[2] - old_pelvis_location[2]),
        # Z
        new_pelvis_location[1] - old_pelvis_location[1]
        
    ))
    # STEP 4: move the camera with the same displacement
    mainCam = bpy.data.objects["Main_cam"]
    mainCam.location += camera_transl
    
def render_video(output_dir, framerate, picture, video, filename_token, render_frame_start, render_frame_length, res_x, res_y):
    main_filepath = ''
    
    scene = bpy.context.scene
    render = scene.render
    
    render.engine = 'CYCLES'
    render.resolution_x=int(res_x)
    render.resolution_y=int(res_y)
    
    render.fps = framerate
    render.frame_map_new = 100
    
    # (Rajmund) NEW: Update camera location to match segment.
    _set_frame_and_reposition_camera(scene, render_frame_start)
    
    if framerate == 24:
        render.frame_map_new = 80
    
    if render.engine == 'WORKBENCH':
        scene.display.shading.show_specular_highlight = False
    
    if render.engine == 'CYCLES': #Defaults
        scene.cycles.device = 'GPU' #CPU
        render.compositor_device = 'GPU'
        scene.cycles.samples = 8 #4096
        scene.cycles.time_limit = 0 #0
        scene.cycles.adaptive_threshold = 0.025 #0.01
        scene.cycles.use_denoising = True
        scene.cycles.denoising_use_gpu = True
        scene.cycles.denoising_prefilter = 'ACCURATE' #ACCURATE #FAST
        scene.cycles.denoising_quality = 'FAST' #HIGH #BALANCED #FAST
        scene.cycles.max_bounces = 0 #12
        scene.cycles.diffuse_bounces = 0 #4
        scene.cycles.glossy_bounces = 0 #4
        scene.cycles.transmission_bounces = 0 #12
        scene.cycles.transparent_max_bounces = 0 #8
        scene.cycles.volume_max_steps = 256 #1024
        render.use_persistent_data = True #False
        scene.world.cycles.sampling_method = 'MANUAL' #AUTO
        scene.world.cycles.sample_map_resolution = 1024 #1024
        scene.world.cycles.max_bounces = 1 #1024
        scene.cycles.use_fast_gi = True #False
        scene.cycles.ao_bounces_render = 1 #1
        scene.world.light_settings.distance = 2 #10
        
        render.use_simplify = False #False
        # scene.cycles.texture_limit_render = 'OFF' #OFF
        # render.simplify_child_particles_render = 1 #1
        # render.simplify_subdivision_render = 6 #6
        
        scene.cycles.use_auto_tile = True #True
        # scene.cycles.tile_size = 1024 #1024
    
    if render_frame_length > 0:
        scene.frame_end = render_frame_start + int(render_frame_length * (render.frame_map_new / 100))
       
    if picture:
        main_filepath = os.path.join(output_dir, '{}'.format(filename_token))
        render.image_settings.file_format='PNG'
        render.image_settings.color_depth = '16'
        create_camera.get_camera('Main_cam')
        render.filepath = main_filepath
        bpy.ops.render.render(write_still=True)
    
    if video:
        main_filepath = os.path.join(output_dir, '{}_'.format(filename_token))
        render.image_settings.file_format='FFMPEG'
        print(f"total_frames {render_frame_length}", flush=True)
        render.ffmpeg.format='MPEG4'
        render.ffmpeg.codec = "H264"
        render.ffmpeg.ffmpeg_preset='REALTIME'
        render.ffmpeg.constant_rate_factor='HIGH'
        render.ffmpeg.audio_codec='MP3'
        render.ffmpeg.gopsize = 30
        scene.display.shading.color_type = 'TEXTURE'
        create_camera.get_camera('Main_cam')
        render.filepath = main_filepath
        bpy.ops.render.render(animation=True)
        
    return main_filepath

def compute_render_time(directory: str) ->str:
    
    renderTime = 0
    
    if directory is not str:
        directory = str(directory)
    
    files = [f for f in os.listdir(directory)]
    for file in files:
        # print(os.path.splitext(file)[0])
        SMPLX_TAKE = myPath(str(directory) + '/' + os.path.splitext(file)[0] + '.npz')
        file_arr = np.load(SMPLX_TAKE, allow_pickle=True)
        renderTime = renderTime + len(file_arr['poses'])
    
    return renderTime

def detect_files(directory: str) ->str:
    
    if directory is not str:
        directory = str(directory)
    
    files = [f for f in os.listdir(directory)]
    return files

def set_char_texture(SMPLX_TAKE):
    if SMPLX_TAKE is None:
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_f_alb.png'
        return
    
    # File format must start with 1_name_0_#_#_... .npz, otherise this will fail
    char_name_mid = re.search(r'(\d+_[a-zA-Z]+)', SMPLX_TAKE.stem)
    char_name = re.match(r"(\d+)_([a-zA-Z]+)", char_name_mid.group(1))
    
    print(char_name_mid)
    print(char_name)
    
    female_names = ['kieks', 'ayana', 'luqi', 'hailing', 'kexin', 'goto', 'yingqing', 'tiffnay', 'katya', 'carla', 'sophie', 'miranda']
    male_names = ['wayne', 'nidal', 'zhao', 'lu', 'carlos', 'jorge', 'itoi', 'daiki', 'li', 'scott', 'solomon', 'lawrence', 'stewart']
    
    texture_type = 'male'
    if char_name.group(2) in female_names:
        texture_type = 'female'
        print(texture_type)
    
    if texture_type == 'female':
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_m_alb.png'
    else:
        bpy.data.window_managers['WinMan'].smplx_tool.smplx_texture = 'smplx_texture_f_alb.png'
        
    bpy.ops.object.smplx_set_texture()

def _load_hair_and_mask(smplx_char):
    hair_blend_file_path = os.path.join(PATHS["SCRIPT_DIR"], 'environments/smplx_genea_male_simplified.blend')
    meshes_to_import = ["mask_male", "male_hair"]  # Replace with actual names

    if os.path.isfile(hair_blend_file_path):
        with bpy.data.libraries.load(hair_blend_file_path, link=False) as (data_from, data_to):
            data_to.objects = [mesh for mesh in data_from.objects if mesh in meshes_to_import]  # Load all available objects
            print(list(data_from.objects))
            print(data_to.objects)
            
        # Link the imported objects to the active collection
        for obj in data_to.objects:
            if obj is not None:
                print(obj)
                obj.rotation_euler[0] -= 1.64
                obj.location = (-0.0125, -0.075, 0.0925)
                bpy.context.collection.objects.link(obj)
                obj.parent = smplx_char
                obj.parent_type = "BONE"
                obj.parent_bone = "head"
                
        obj.location = (-0.005, -0.03, -0.05)

def _create_scene_and_load_smplx(smplx_file):       
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.smplx_add_animation(filepath=str(smplx_file))
    # bpy.ops.object.smplx_reset_expression_shape()
    # bpy.ops.object.smplx_reset_poseshapes()
    bpy.ops.object.select_all(action='DESELECT')
    
    set_char_texture(smplx_file)
    
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            smplx_char = obj
            break
        
    # Add hair and mask
    _load_hair_and_mask(smplx_char)

    pelvis_bone = smplx_char.pose.bones['pelvis']
    smplx_mesh = smplx_char.children[0]
    
    bpy.context.object.modifiers["Armature"].use_deform_preserve_volume = True
    
    create_material.setup_subdivision_surface(smplx_mesh)
    create_material.setup_material_nodes(smplx_mesh, script_dir)
    create_material.setup_geometry_nodes(smplx_mesh)

    bpy.context.scene.sequence_editor_create()

    create_scene.setup_scene(
        cam_pos = Vector((
            pelvis_bone.location[0], 
            pelvis_bone.location[1], 
            pelvis_bone.location[2])) + Vector((0, -0.375, 4)
        ),
        cam_rot = [0, 0, 0],
        plane_size = 10,
        InLocation = [0, 5, 15])

    bpy.ops.object.select_all(action='DESELECT')
    
    smplx_char.select_set(True)
    mainCam = bpy.data.objects['Main_cam']
    mainCam.select_set(True)
    
    
    bpy.ops.transform.rotate(value=-1.57, orient_axis='X')
    
    mainCam.location[1] += 1.875
    mainCam.location[2] += 0.4
    
    return smplx_char

def _load_audio_in_scene(audio_dir, smplx_file, args):
    audio_path = audio_dir / myPath(str(smplx_file.stem) + '.wav')
    try:
        audio_path
    except:
        audio_path = ''
    
    if audio_path: # Rajmund: I temporarily removed "and not IS_SERVER"
        load_data.load_audio(str(audio_path), 1)

def main_ui(AUDIO_LOCATION_IN, SMPLX_TAKE_IN: myPath, args: dict):
    """
    This is the main visualisation scripts that should get called in the Blender UI.
    """
    start = time.time()
    
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')

    print('[INFO] Script is running from command line.') 
    print('ARG_OUTPUT_DIR: ', args['output_dir'])
    assert "." not in str(args['output_name']), "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in str(args['output_name']) and "\\" not in str(args['output_name']), "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""
    
    if not os.path.exists(str(args['output_dir'])):
        os.mkdir(str(args['output_dir']))
    
    smplx_char = _create_scene_and_load_smplx(SMPLX_TAKE_IN)
    _load_audio_in_scene(AUDIO_LOCATION_IN, SMPLX_TAKE_IN, args)
    
    for segment_number in range(len(args['start'])):
        duration = args['duration'][segment_number]
        if duration == -1:
            duration = smplx_char.animation_data.action.frame_range.y
            
        render_video(
            str(args['output_dir']),
            args['framerate'],
            args['png'], 
            args['video'], 
            smplx_char.name,
            args['start'][segment_number],
            duration, 
            args['res_x'], 
            args['res_y'])
                
    end = time.time()
    all_time = end - start
    # print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    print(all_time)


def main_cmd(AUDIO_LOCATION_IN, SMPLX_TAKE_IN: myPath, args: dict):
    """
    This is the main visualisation script that should get called from the cmd line.
    """
    start = time.time()
    
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')

    print('[INFO] Script is running from command line.') 
    print('ARG_OUTPUT_DIR: ', args['output_dir'])
    assert "." not in str(args['output_name']), "No period (.) allowed in the output filename. The script sets the extensions automatically."
    assert "/" not in str(args['output_name']) and "\\" not in str(args['output_name']), "No directories allowed in output filename. Filename contains a slash \"/\" or \"\\\""
    
    if not os.path.exists(str(args['output_dir'])):
        os.mkdir(str(args['output_dir']))
    
    smplx_char = _create_scene_and_load_smplx(SMPLX_TAKE_IN)
    _load_audio_in_scene(AUDIO_LOCATION_IN, SMPLX_TAKE_IN, args)
    
    for segment_number in range(len(args['start'])):
        duration = args['duration'][segment_number]
        if duration == -1:
            duration = smplx_char.animation_data.action.frame_range.y
            
        render_video(
            str(args['output_dir']),
            args['framerate'],
            args['png'], 
            args['video'], 
            smplx_char.name,
            args['start'][segment_number],
            duration, 
            args['res_x'], 
            args['res_y'])
                
    end = time.time()
    all_time = end - start
    # print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    print(all_time)

def load_environment():
    """Load the indoor scene from a prepared .blend file."""
    blend_file_path = os.path.join(PATHS["SCRIPT_DIR"], 'environments/IndoorEnvironment_smaller.blend')

    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
        data_to.objects = list(data_from.objects)  # Load all available objects

    # Link the imported objects to the active collection
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)

def render_segments_in_ui():
    """ 
    Render BEAT-2 segments specified via a so-called metadata .csv file with the following structure:
    >>>
        file_name,start_frame,duration_frame
        10_kieks_0_103_103,0,293
        ...
        11_nidal_0_95_95,1661,333
    <<<
    """
    print('[INFO] Script is running in Blender UI.')
    args = {
        'input_npz_dataset_directory': myPath('D://GENEA_Leaderboard//beat_v2.0.0//beat_v2.0.0//beat_english_v2.0.0'),
        'input_npz_dir': myPath('D://GENEA_Leaderboard//SemanticGesticulator//sample_1'),
        'segment_csv': myPath('D://GENEA_Leaderboard//segment_metadata_sample.csv'),
        'output_dir': myPath('D://GENEA_Leaderboard//_RENDER_OUTPUTS_SG_SAMPLE_2'),
        'start': [1661], # specified in frames
        'duration': [15], # specified in frames
        'png': False,
        'video': True,
        'res_x': 1440,
        'res_y': 1080,
        'framerate': 30,
        'render_time': False,
        'update_config': False
    }
    metadata_df = pd.read_csv(args['segment_csv'], header="infer").groupby("file_name").agg(list)
    for file_id, row in metadata_df.iterrows():
        # Check the validity of the input file
        ARG_NPZ_FILE = load_data.check_files_npz(args['input_npz_dir'], file_id, join(args['input_npz_dataset_directory'], "smplxflame_30"), file_id) 
        
        # Overwrite start and duration timestamps
        args['start'] = row["start_frame"] # This is a list of start frames
        args['duration'] = row["duration_frame"] # This is a list of segment durations in frames
        
        # Run rendering
        audio_dir = myPath(join(args['input_npz_dataset_directory'], "wave16k"))
        smplx_file = myPath(join(args['input_npz_dir'], ARG_NPZ_FILE))

        main_ui(audio_dir, smplx_file, args=args)
        create_scene.clear_character()

def render_segments_in_cmd():
    """
    Render BEAT-2 SMPL-X files through the command line.
    This script can be run in three ways:
        1) Provide a single .npz SMPL-X file, possibly paired with audio.
        2) Provide a folder with .npz SMPL-X files, and possibly a folder of audio files. Each file is rendered in full length.
        3) Provide a .csv file with filenames and segment start/duration information, and possibly a folder of audio files. Each row in the .csv file defines a short clip that will be rendered.
    """
    args = parser.parse_args()    
    file_path = myPath(join(args['input_npz_dataset_directory'], "train_test_split.csv"))
    matches = load_data.filter_csv_by_type(file_path, match_type="test")
    # unique_names_list, unique_ids_list, unique_entry_list = load_data.extract_unique_names(matches)
    
    # Mode 3: Load segments from a .csv file.    
    if args['segment_csv'] is not None:
        # Pre-check
        if args['input_npz_dir'] is None or args['input_npz'] is not None:
            print('ERROR: Segment metadata csv is provided, but `input_npz` is also provided or `input_npz_dir` is missing. Please make sure only the latter is provided when rendering segments using the csv input file.')
            exit()
        
        metadata_df = pd.read_csv(args['segment_csv'], header="infer").groupby("file_name").agg(list)
        for file_id, row in metadata_df.iterrows():
            # Check the validity of the input file
            ARG_NPZ_FILE = load_data.check_files_npz(args['input_npz_dir'], file_id, join(args['input_npz_dataset_directory'], "smplxflame_30"), file_id) 
            
            # Overwrite start and duration timestamps
            args['start'] = row["start_frame"] # This is a list of start frames
            args['duration'] = row["duration_frame"] # This is a list of segment durations in frames
            
            # Run rendering
            audio_dir = myPath(join(args['input_npz_dataset_directory'], "wave16k"))
            smplx_file = myPath(join(args['input_npz_dir'], ARG_NPZ_FILE))
            
            main_cmd(audio_dir, smplx_file, args=args)
            create_scene.clear_character()
    
    else:
        exit("TODO: Only segment csv input works for now.")          
                
        

        SMPLX_LOCATION = ARG_NPZ_DIR
        # SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/' + SMPLX_FILENAME_IN + '.npz')
        # print('write data to this one: ' + str(SMPLX_TAKE))
        
        if args['render_time'] is not False:
            renderTime = 0
            renderTime = compute_render_time(str(SMPLX_LOCATION))
            print(renderTime)
            print(float(renderTime/60/60/30))
            exit()
        
        files = [f for f in os.listdir(SMPLX_LOCATION)]
        i = 0
        
        for file in files:
            
            if not file.endswith(".npz"):
                continue
            
            # This needs to check for filename comparison and such
            ARG_NPZ_FILE = load_data.check_files_npz(SMPLX_LOCATION, os.path.splitext(file)[0], args['input_npz_dataset_directory'], ARG_NPZ_DATASET_FILENAME)
            print(ARG_NPZ_FILE)
            main(ARG_AUDIO_LOCATION, SMPLX_TAKE_IN=ARG_NPZ_FILE)
            create_scene.clear_character()
            
        if ARG_NPZ_FILE is not None and ARG_NPZ_DIR is not None:
            print('Please provide either a specific file or a directory of files. Not both at the same time!')
            exit()
        
        if ARG_NPZ_FILE is not None:
            ARG_NPZ_FILE = load_data.check_files_npz(ARG_NPZ_FILE.parent, ARG_NPZ_FILE.stem, args['input_npz_dataset_directory'], ARG_NPZ_DATASET_FILENAME)
            print(ARG_NPZ_FILE)
            main(ARG_AUDIO_LOCATION, SMPLX_TAKE_IN=ARG_NPZ_FILE)
            create_scene.clear_character()
            
        if ARG_NPZ_DIR is not None:
            SMPLX_LOCATION = ARG_NPZ_DIR
            # SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/' + SMPLX_FILENAME_IN + '.npz')
            # print('write data to this one: ' + str(SMPLX_TAKE))
            
            if args['render_time'] is not False:
                renderTime = 0
                renderTime = compute_render_time(str(SMPLX_LOCATION))
                print(renderTime)
                print(float(renderTime/60/60/24))
                exit()
            
            files = [f for f in os.listdir(SMPLX_LOCATION)]
            i = 0
            
            for file in files:
                
                if not file.endswith(".npz"):
                    continue
                
                # This needs to check for filename comparison and such
                ARG_NPZ_FILE = load_data.check_files_npz(SMPLX_LOCATION, os.path.splitext(file)[0], args['input_npz_dataset_directory'], ARG_NPZ_DATASET_FILENAME)
                print(ARG_NPZ_FILE)
            
                main(ARG_AUDIO_LOCATION, SMPLX_TAKE_IN=ARG_NPZ_FILE)
                create_scene.clear_character()

# START OF CODE
all_start = time.time()
create_scene.clear_scene()

if bpy.ops.text.run_script.poll():
    PATHS = {
        "SCRIPT_DIR" : myPath(bpy.context.space_data.text.filepath).parents[0],
        "ROOT_DIR" : myPath(bpy.context.space_data.text.filepath).parents[1],
    }
else:
    PATHS = {
        "SCRIPT_DIR" : myPath(os.path.realpath(__file__)).parents[0],
        "ROOT_DIR" : myPath(os.path.realpath(__file__)).parents[1],
    }
load_environment()
# bpy.utils.register_class(SequentialRenderOperator)
# bpy.ops.render.sequential_animations()

if bpy.ops.text.run_script.poll():
    render_segments_in_ui()
else:
    args = parser.parse_args()
    parser.check_args(args)
    
    render_segments_in_cmd()
    
