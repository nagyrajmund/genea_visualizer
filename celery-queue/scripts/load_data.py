import bpy
from pathlib import Path as myPath
import importlib
import os
import numpy as np
import csv
import re

if bpy.ops.text.run_script.poll():
    script_dir = myPath(bpy.context.space_data.text.filepath).parents[0]
else:
    script_dir = myPath(os.path.realpath(__file__)).parents[0]

import edit_character
importlib.reload(edit_character)

def load_audio(filepath, name):
    audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip' + str(name),
        filepath=filepath,
        channel=name,
        frame_start=0
    )
    
def load_fbx(filepath, name):
    print(script_dir)
    bpy.ops.import_scene.fbx(
        filepath=filepath, 
        ignore_leaf_bones=True, 
        force_connect_children=True, 
        automatic_bone_orientation=False
    )
    edit_character.remove_bone(
        bpy.data.objects['Armature'], 
        'b_r_foot_End'
    )
    bpy.data.objects['Armature'].name = name
        
def load_bvh(filepath):
    bpy.ops.import_anim.bvh(
        filepath=filepath, 
        use_fps_scale=False,
        update_scene_fps=False, 
        update_scene_duration=True, 
        global_scale=0.01
    )
    
def check_files_npz(SMPLX_LOCATION, SMPLX_FILENAME, SMPLX_LOCATION_DATASET = None, SMPLX_FILENAME_DATASET = None) -> myPath:
    SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/' + str(SMPLX_FILENAME) + '.npz')
    smplx_loaded_data = np.load(SMPLX_TAKE, allow_pickle=True)
    
    SMPLX_TAKE_DATASET = myPath(str(SMPLX_LOCATION_DATASET) + '/' + str(SMPLX_FILENAME_DATASET) + '.npz')
    
    
    smplx_dataset_data = np.load(SMPLX_TAKE_DATASET, allow_pickle=True)
    
    # speaker = SMPLX_FILENAME.split("_")[1]
    # speaker_heights = {'ayana': 1.09, 'carla': 1.36, 'carlos': 1.19, 'daiki': 1.34, 'goto': 1.12, 'hailing': 1.21, 'itoi': 1.26, 'jorge': 1.38, 
    #                    'katya': 1.12, 'kexin': 1.11, 'kieks': 1.29, 'lawrence': 1.28, 'li': 1.34, 'lu': 1.26, 'luqi': 1.21, 'miranda': 1.21, 'nidal': 1.41, 
    #                    'scott': 1.31, 'solomon': 1.45, 'sophie': 1.2, 'stewart': 1.33, 'tiffnay': 1.17, 'wayne': 1.38, 'yingqing': 1.2, 'zhao': 1.34}
    
    # CORRECT .NPZ
    os.makedirs(str(SMPLX_LOCATION) + '/body_shape', exist_ok=True)
    
    updated = {**smplx_dataset_data}
    # The motion is taken from the input file
    updated['poses'] = smplx_loaded_data['poses']
    updated['trans'] = smplx_loaded_data['trans']
    # Facial expressions are zeroed out
    updated['expressions'] = np.zeros((len(smplx_loaded_data['poses']), 100), dtype=float)
    # These parameters are constant for the visualiser
    updated['mocap_frame_rate'] = 30
    updated['model'] = "smplx2020"
    updated['gender'] = "neutral"
    np.savez(os.path.join(str(SMPLX_LOCATION) + '/body_shape/', SMPLX_FILENAME),
             **updated)
    SMPLX_TAKE = myPath(str(SMPLX_LOCATION) + '/body_shape/' + SMPLX_FILENAME + '.npz')
    print(SMPLX_TAKE)
    
    return SMPLX_TAKE

def extract_segment(file_name):
    try:
        # Remove the file extension
        base_name = file_name.rsplit('.', 1)[0]
#        print(base_name)
        # Split by underscores
        parts = base_name.split('_')
#        print(parts)
        # Extract the required segment
        result = '_'.join(parts[2:7])  # Indices 1 to 5 (inclusive)
        return result
    except IndexError:
        print("Error: The filename format doesn't match the expected convention.")
        return None

def filter_csv_by_type(file_path, match_type="test"):
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            result = [row['id'] for row in reader if row['type'] == match_type]
        return result
    except Exception as e:
        print(f"Error: {e}")
        return []

def extract_unique_names(file_path):
    unique_names = {}
    unique_ids = {}
    unique_list = {}
    
    # with open(file_path, "r") as file:
    for line in file_path:
        # Search for names in the pattern: number_name
        match = re.search(r'(\d+_[a-zA-Z]+)', line)
        if match:
            idname = match.group(1)
            
            match2 = re.match(r"(\d+)_([a-zA-Z]+)", idname)
            id = match2.group(1)
            name = match2.group(2)
            
            # Check if "test" is in the same line (assuming it's in the next column)
            if name not in unique_names:
                unique_names[name] = line.strip() 
                unique_ids[id] = line.strip() # Store the full matching line if needed
                unique_list[idname] = line.strip()

    return list(unique_names.keys()), list(unique_ids.keys()), list(unique_list.values())