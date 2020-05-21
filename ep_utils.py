import os
import numpy as np
import pickle

#### IMPORTING BLENDSHAPES
def load_mesh(character, target=False, triangles=False):

    character_neutral_path = get_neutral_obj_path(character, target)

    if triangles == False:
        # character = character.lower()

        if target:
            character_neutral = np.array(get_vertices_from_obj(character_neutral_path))
            print("loaded target vertices: " + str(len(character_neutral)))
            return character_neutral

        if character == 'johnny':
            print("Loading Character " + character)
            with open ('./meshes/blendshapes_' + character + '.txt', 'rb') as f:
                character_blendshapes = np.array(pickle.load(f))
            print(character_blendshapes.shape)
            character_neutral = character_blendshapes[0]
            character_blendshapes = character_blendshapes[1:]
        else:
            character_blendshapes_folder = get_blendshapes_folder(character)
            character_neutral = np.array(get_vertices_from_obj(character_neutral_path))
            character_blendshapes = np.array(get_vertices_all_objs(character_blendshapes_folder))
        # elif character == 'macaw' or character == 'mateo':
        #     character_neutral = np.array(get_vertices_from_obj(os.path.join('meshes/' + character, character + '_neutral.obj')))
        #     character_blendshapes = np.array(get_vertices_all_objs('meshes/' + character))
        # elif character == 'billy'or character == 'loki' or character == 'mery':
        #     character_neutral = np.array(get_vertices_from_obj(os.path.join('meshes/ExamplesMeshes/' + character, character + '_neutral.obj')))
        #     character_blendshapes = np.array(get_vertices_all_objs('meshes/ExamplesMeshes/' + character))
        #     print(character_blendshapes.shape)
        # else:
        #     print("Unknown character: " + str(character))
        #     exit(1)
        print("loaded source vertices: " + str(len(character_neutral)))
        print("loaded source blendshapes: " + str(len(character_blendshapes)))
        return (character_neutral, character_blendshapes)

    elif triangles == True:
        # character = character.lower()

        if target:
            tris = get_triangles_obj('./target_meshes/' + character + '.obj')
            return tris

        tris = get_triangles_obj(character_neutral_path)

        # if character == 'johnny':
        #     print("I haven't implemented loading triangles for this character yet.")
        #     exit(1)
        # elif character == 'macaw' or character == 'mateo':
        #     tris = get_triangles_obj('meshes/' + character + '/' + character + '_neutral.obj')
        # elif character == 'billy'or character == 'loki' or character == 'mery':
        #     tris = get_triangles_obj('meshes/ExamplesMeshes/' + character + '/' + character + '_neutral.obj')
        # else:
        #     print("Unknown character: " + str(character))
        #     exit(1)
        return tris

def get_vertices_from_obj(obj_file):
    with open (obj_file, 'r') as f:
        #blendshapes = f.readlines()
        contents = f.read()
        mesh_info = contents.splitlines()
        mesh_info = list(filter(None, mesh_info)) # remove blank lines

    verts = []

    for line in mesh_info:
        if line[0:2] == 'v ':
            vert = line.split(' ')
            vert = vert[1:]
            verts.append([float(vert[0]),float(vert[1]),float(vert[2])])

    # print("returning " + str(len(verts)) + " verts")

    return verts

def get_vertices_all_objs(folder):
    with open (os.path.join(folder, 'blendshapes.txt'), 'r') as f:
        #blendshapes = f.readlines()
        contents = f.read()
        blendshapes = contents.splitlines()

    # neutral_vertices = get_vertices_from_obj(os.path.join(folder, neutral))
    blendshape_vertices = []
    for bs in blendshapes:
        blendshape_vertices.append(get_vertices_from_obj(os.path.join(folder, bs + '.obj')))

    # all_shapes = [neutral_vertices] + blendshape_vertices
    return blendshape_vertices

def get_triangles_obj(obj_file):
    # returns the vertex indices for triangles
    
    with open (obj_file, 'r') as f:
        #blendshapes = f.readlines()
        contents = f.read()
        mesh_info = contents.splitlines()
        mesh_info = list(filter(None, mesh_info)) # remove blank lines

    faces = []

    for line in mesh_info:
        if line[0] == 'f':
            face = line.split(' ')
            face = face[1:]
            face_clean = []
            for compound_info in face:
                face_clean.append(int(compound_info.split('/')[0]))
            faces.append(face_clean)

    print("returning " + str(len(faces)) + " faces")

    return faces

def load_obj(obj_file, return_face_info=False):

    with open (obj_file, 'r') as f:
        #blendshapes = f.readlines()
        contents = f.read()
        mesh_info = contents.splitlines()
        mesh_info = list(filter(None, mesh_info)) # remove blank lines

    verts = []
    texs = []
    norms = []
    faces = []
    vert_faces = []
    tex_faces = []
    norm_faces = []

    for line in mesh_info:
        if line[0:2] == 'v ':
            vert = line.split(' ')
            vert = vert[1:]
            verts.append([float(vert[0]),float(vert[1]),float(vert[2])])
        elif line[0:2] == 'vt':
            tex = line.split(' ')
            tex = tex[1:]
            texs.append([float(tex[0]),float(tex[1])])
        elif line[0:2] == 'vn':
            norm = line.split(' ')
            norm = norm[1:]
            norms.append([float(norm[0]),float(norm[1]),float(norm[2])])
        elif line[0] == 'f':
            face = line.split(' ')
            face = face[1:]
            faces.append(face)
            clean_vert_faces = []
            clean_tex_faces = []
            clean_norm_faces = []
            for compound_info in face:
                v_t_n = compound_info.split('/')
                clean_vert_faces.append(int(v_t_n[0]))
                clean_tex_faces.append(int(v_t_n[1]))
                clean_norm_faces.append(int(v_t_n[2]))
            vert_faces.append(clean_vert_faces)
            tex_faces.append(clean_tex_faces)
            norm_faces.append(clean_norm_faces)

    # print("num verts: " + str(len(verts)))
    # print("num norms: " + str(len(norms)))
    ordered_verts = verts
    ordered_texs = texs
    ordered_norms = norms

    if return_face_info:
        return (verts,texs,norms,faces)

    # reorder verts and norms based on faces
    # if len(ordered_verts) > 0:
        # ordered_verts = []
        # for face in vert_faces:
        #     ordered_verts.extend(verts[face[0]-1])
        #     ordered_verts.extend(verts[face[1]-1])
        #     ordered_verts.extend(verts[face[2]-1])

    # if len(ordered_texs) > 0:
    #     ordered_texs = []
    #     for face in tex_faces:
    #         ordered_texs.extend(texs[face[0]-1])
    #         ordered_texs.extend(texs[face[1]-1])
    #         ordered_texs.extend(texs[face[2]-1])

    # if len(ordered_norms) > 0:
    #     ordered_norms = []
    #     for face in norm_faces:
    #         ordered_norms.extend(norms[face[0]-1])
    #         ordered_norms.extend(norms[face[1]-1])
    #         ordered_norms.extend(norms[face[2]-1])

    ordered_verts = reorder_by_index(verts, vert_faces)
    ordered_texs = reorder_by_index(texs, tex_faces)
    ordered_norms = reorder_by_index(norms, norm_faces)

    # print("num ordered verts: " + str(len(ordered_verts)))
    # print("num ordered norms: " + str(len(ordered_norms)))

    return (ordered_verts,ordered_texs,ordered_norms)

def reorder_by_index(data_array, index_array):
    ordered_data = []
    for index in index_array:
        ordered_data.extend(data_array[index[0]-1])
        ordered_data.extend(data_array[index[1]-1])
        ordered_data.extend(data_array[index[2]-1])
    return ordered_data

def get_indices_from_faces(faces):
    vert_faces = []
    tex_faces = []
    norm_faces = []
    for face in faces:
        clean_vert_faces = []
        clean_tex_faces = []
        clean_norm_faces = []
        for compound_info in face:
            v_t_n = compound_info.split('/')
            clean_vert_faces.append(int(v_t_n[0]))
            clean_tex_faces.append(int(v_t_n[1]))
            clean_norm_faces.append(int(v_t_n[2]))
        vert_faces.append(clean_vert_faces)
        tex_faces.append(clean_tex_faces)
        norm_faces.append(clean_norm_faces)
    return (vert_faces, tex_faces, norm_faces)

def get_ordered_data(verts, texs, norms, faces):
    (vert_faces, tex_faces, norm_faces) = get_indices_from_faces(faces)
    ordered_verts = reorder_by_index(verts, vert_faces)
    ordered_texs = reorder_by_index(texs, tex_faces)
    ordered_norms = reorder_by_index(norms, norm_faces)

def save_obj(filepath, filename, vs, ts, ns, fs=[]):
    contents = ""

    for v in vs:
        contents += "v %f %f %f\n" % (v[0],v[1],v[2])
    for t in ts:
        contents += "vt %f %f\n" % (t[0],t[1])
    for n in ns:
        contents += "vn %f %f %f\n" % (n[0],n[1],n[2])
    for f in fs:
        contents += "f %s %s %s\n" % (f[0],f[1],f[2])

    with open (filepath + filename + ".obj", 'w') as f:
        f.write(contents)


# create an expression given a rig and blendshape indices
def combine_blendshapes(neutral, blendshape_deltas, blendshape_indices):
    expression = neutral.copy()
    for index in blendshape_indices:
        expression += blendshape_deltas[index]
    return expression

# save a set of expressions
def save_expressions_obj(character, blendshape_deltas, expressions, obj_filepath):
    print("loading target neutral")
    (verts,texs,norms,faces) = load_obj(get_neutral_obj_path(character, True), True)
    expression_index = 0
    for expression in expressions:
        out_verts = combine_blendshapes(verts, blendshape_deltas, expression)
        obj_name = str(expression_index)
        save_obj(obj_filepath, obj_name, out_verts, texs, norms, faces)
        expression_index += 1


# create config file for EBFR
def create_ebfr_config_file(config_file_location, method, source_neutral_location, target_neutral_location, source_blendshapes_location, examples_location, examples_blendshapes, results_location, config_file_name):
    print("Creating config file")

    content = ""

    # add method
    content += "method " + method + '\n'

    # add source and target neutrals
    content += "source_undeformed " + source_neutral_location + '\n'
    content += "target_undeformed " + target_neutral_location + '\n'

    # add blank space
    content += '\n'

    # add blendshapes
    with open (os.path.join(source_blendshapes_location, 'blendshapes.txt'), 'r') as f:
        contents = f.read()
        blendshapes = contents.splitlines()
    for bs in blendshapes:
        content += "source_deformed " + source_blendshapes_location + bs + ".obj" + '\n'

    # add blank space
    content += '\n'

    # add examples
    for i in range(len(examples_blendshapes)):
        content += "example " + examples_location + str(i) + ".obj" + '\n'

    # add blank space
    content += '\n'

    # add weights
    # format - each line = blendshape, each number = expression
    # i.e. if a blendshape exists in expression N, the Nth number in that blendshape's row will be set (to 1.0 in our case, as we always fully activate blendshapes)
    for i in range(len(blendshapes)):
        content += "weight "
        for example in examples_blendshapes:
            if i in example:
                content += "1.0 "
            else:
                content += "0.0 "
        content += '\n'

    # add blank space
    content += '\n'

    # add lines saying which blendshapes are included/not included
    shapes_covered = list(set([shape for example in examples_blendshapes for shape in example]))
    shapes_not_covered = [shape for shape in list(range(len(blendshapes))) if shape not in shapes_covered]
    print("shapes_covered " + str(shapes_covered))
    print("shapes_not_covered " + str(shapes_not_covered))
    content += "shapes_covered " + str(shapes_covered) + '\n'
    content += "shapes_not_covered " + str(shapes_not_covered) + '\n'

    # add blank space
    content += '\n'

    # add result destination file
    content += "location_target_deformed ./ebfr_results/" + results_location

    with open (os.path.join(config_file_location, config_file_name + '.txt'), 'w') as f:
        f.write(content)

    print("Config file created")

def save_results_list(results):
    with open ('./results.txt', 'w') as f:
        f.write(str(results))

# returns path relative to python file!!
def get_neutral_obj_path(character, target=False):
    if target:
        return './target_meshes/' + character + '.obj'

    if character == "mateo_06":
        return './meshes/Mateo/mateo_y_06/mateo_neutral.obj'
    elif character == 'tatiana_reduced':
        return './meshes/tatiana_reduced/tatiana_neutral.obj'

    elif character in ['macaw', 'macaw_dwarf_dissimilar', 'mateo', 'louise', 'louise_tatiana_cor', 'tatiana', 'tatiana_reduced', 'louise_elf_dissimilar', 'new_elf', 'new_dwarf']:
        return './meshes/' + character + '/' + character + '_neutral.obj'
    elif character == 'billy'or character == 'loki' or character == 'mery':
        return './meshes/ExamplesMeshes/' + character + '/' + character + '_neutral.obj'
    else:
        print("No neutral path defined for character: " + str(character))
        exit(1)

def get_blendshapes_folder(character):
    if character == "mateo_06":
        return './meshes/Mateo/mateo_y_06/'

    if character in ['macaw', 'macaw_dwarf_dissimilar', 'mateo', 'louise', 'louise_tatiana_cor', 'tatiana', 'tatiana_reduced', 'louise_elf_dissimilar', 'new_elf', 'new_dwarf']:
        return './meshes/' + character + '/'
    elif character == 'billy'or character == 'loki' or character == 'mery':
        return './meshes/ExamplesMeshes/' + character +'/'
    else:
        print("No blendshapes folder defined for character: " + str(character))
        exit(1)


# used to fix Lousie blendshape indices as I deleted some and so the output needs to be updates
def fix_indices_for_zero_blendshapes(expression):
    # print("fixing output indices for zero blendshapes")
    zero_blendshapes = [107, 111, 154] # HARDCODED FOR LOUISE
    return_expression = expression.copy()
    for i in range(len(return_expression)):
        for zero_bs in zero_blendshapes:
            if return_expression[i] > zero_bs:
                return_expression[i] += 1
    return return_expression

def get_blendshapes_to_print(expression, character = ''):
    # character = 'louise'
    if character in ['mateo', 'mateo_06', 'macaw', 'macaw_dwarf_dissimilar', 'new_dwarf']:
        return [(i if i < 23 else i+1) for i in expression]
    elif character in ['louise', 'louise_elf_dissimilar', 'new_elf']:
        return fix_indices_for_zero_blendshapes(expression)
    else:
        # print("no printing rule defined for this source character")
        return expression

def flatten(a):
    return [i for thing in a for i in thing]

def calculate_lens(opt, greed):
    opt5 = flatten(opt[:5])
    opt10 = flatten(opt[:10])
    opt15 = flatten(opt[:15])
    opt20 = flatten(opt[:20])

    greed5 = flatten(greed[:5])
    greed10 = flatten(greed[:10])
    greed15 = flatten(greed[:15])
    greed20 = flatten(greed[:20])

    print("lens opt: ")
    for thingy in [opt5, opt10, opt15, opt20]:
        print(len(thingy))


    print("lens greed: ")
    for thingy in [greed5, greed10, greed15, greed20]:
        print(len(thingy))

    print("overlaps: ")
    print(len(set(opt5) & set(greed5)))
    print(len(set(opt10) & set(greed10)))
    print(len(set(opt15) & set(greed15)))
    print(len(set(opt20) & set(greed20)))