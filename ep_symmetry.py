import numpy as np
import pickle
import os
import ep_utils
import math

def import_symmetry_groups(character):
    filepath = "./symmetries/"
    symmetry_group_vertices = []

    for i in range(8):
        sym_file = filepath + character + "_syms" + str(i) + ".txt"
        #print("attempting to open file: " + sym_file)
        if os.path.isfile(sym_file):
            with open (sym_file, "rb") as f:
                group = pickle.load(f)
                symmetry_group_vertices.append(group)
        else:
            print("NO SYMMETRY GROUPS DEFINED")
            exit(1)
            
    return symmetry_group_vertices


def remove_intersections(sets):
    intersection = set(sets[0]) & set(sets[1])

    for item in intersection:
        sets[0].remove(item)
        sets[1].remove(item)

    return sets

def find_blendshapes_in_symmetry_groups(character, delta_blendshapes): # delta_blendshapes here is binary blendshapes, should rename
    blendshape_symmetry_groups = []

    symmetry_group_vertices = import_symmetry_groups(character)

    for group in symmetry_group_vertices:
        # for each group of vertices, we count how many of those vertices are activated for each blendshape
        blendshape_vertex_count = [0 for i in range(len(delta_blendshapes))]
        blendshape_group = []

        for i in range(len(delta_blendshapes)):
            for v in group:
                if delta_blendshapes[i][v] == 1:
                    blendshape_vertex_count[i] += 1
            if blendshape_vertex_count[i] > 0.01*sum(delta_blendshapes[i]):
                blendshape_group.append(i)
        blendshape_symmetry_groups.append(blendshape_group)

    blendshape_symmetry_groups = [list(set(i)) for i in blendshape_symmetry_groups]

    eye_l_groups = remove_intersections(blendshape_symmetry_groups[:2])
    eye_r_groups = remove_intersections(blendshape_symmetry_groups[2:4])
    mouth_groups = remove_intersections(blendshape_symmetry_groups[4:6])
    face_groups = remove_intersections(blendshape_symmetry_groups[6:8])

    return eye_l_groups + eye_r_groups + mouth_groups + face_groups



def find_all_symmetric_blendshape(bs_index, bs_displacements, symmetry_groups, axis, not_axis=[1,1,1]):
    group_to_check = []
    symmetric_blendshapes = []

    for i in range(len(symmetry_groups)):
        if bs_index in symmetry_groups[i]:
            if i%2 == 0:
                group_to_check = symmetry_groups[i+1]
            else:
                group_to_check = symmetry_groups[i-1]

    bs_disp = bs_displacements[bs_index]
    possible_symmetries = np.array(bs_displacements)[group_to_check]

    # we want to always invert movement perp to axis, then always check for dot == 1
    bs_disp *= np.array(not_axis)

    # check dot products
    sym_bs = []
    index = 0
    for bs in possible_symmetries:

        # want to check magnitudes
        bs_disp_mag = np.linalg.norm(bs_disp)
        bs_mag = np.linalg.norm(bs)

        # need to normalise first
        bs_disp_norm = bs_disp/bs_disp_mag
        bs_norm = bs/bs_mag

        # get dot of normalised direction vectors
        dot_prod = np.dot(bs_disp_norm, bs_norm)

        # weight by ratio of magnitudes
        mag_ratio = max(bs_disp_mag/bs_mag, bs_mag/bs_disp_mag)
        dot_prod_value = dot_prod * (1/mag_ratio)

        # save all blendshapes over 0.985, ~10 degree difference
        if dot_prod > 0.985:
            # but save weighted dot for ordering
            sym_bs.append((dot_prod_value, group_to_check[index]))
        index += 1

    # undo the inversion used for previous checks!
    bs_disp *= np.array(not_axis)

    # we want to return as is, as we'll sort when ALL symmetries are found
    return sym_bs

    # # order blendshapes by symmetry
    # sym_bs.sort()

    # # strip dot product as we only want blendshapes
    # sym_bs_stripped = [j for (i,j) in sym_bs]

    # return sym_bs_stripped




def find_symmetric_blendshapes_from_pairs(bs_index, symmetry_pairs, current_indices):
    ### ONE LIST, EACH ELEMENT HAS ONE L/R and ONE TOP/BOT, RETURN EACH + SYMMETRIC OF ONE OTHER IF EXISTS
    return_list = []
    for pair in symmetry_pairs:
        if bs_index in pair:
            check_pair = pair.copy()
            check_pair.remove(bs_index)
            if check_pair[0] in current_indices:
                return_list.append(check_pair[0])

    # print("direct pairs", return_list)

    return_list = list(set(return_list))
    check_list = return_list.copy()

    for pair in symmetry_pairs:
        for bs in check_list:
            if bs in pair and bs_index not in pair:
                check_pair = pair.copy()
                check_pair.remove(bs)
                if check_pair[0] in current_indices:
                    return_list.extend(check_pair)

    return list(set(return_list))




def get_symmetry_pairs(symmetry_groups, bs_displacements, source_character="", bs_diffs=[], vertex_activation_all=[]):

    if source_character == "":
        # we want to basically get all pairs in order of most symmetric -> least symmetric, which is what the following function does
        unpruned_pairs = get_symmetry_pairs_multiple(symmetry_groups, bs_displacements)

        print("unpruned pairs: " + str(unpruned_pairs)) # THIS IS 2 LISTS, LOCAL AND GLOBAL

        # then, we want to ensure each blendshape only occurs in ONE symmetry pair for both local and global (i.e. we can have local pair [0,1] and global pair [0,2], but not two local pairs [0,1], [1,3])
        # return_pairs = []
        # for pair_list in unpruned_pairs:
        #     pruned = []
        #     # print("list being pruned: " + str(pair_list))
        #     all_indices = list(range(len(bs_displacements)))
        #     for pair in pair_list:
        #         pruned.append(pair)
        #         # print("checking pair: " + str(pair))
        #         for item in pair:
        #             # print("checking item: " + str(item))
        #             if item in all_indices:
        #                 all_indices.remove(item)
        #                 # print("item found, removing")
        #             else:
        #                 pruned.remove(pair)
        #                 # print("item not found, already found in previous pair, removing pair")
        #                 break
        #     return_pairs.append(pruned)

    else:
        unpruned_pairs = get_symmetry_pairs_multiple(symmetry_groups, bs_displacements)
        unpruned_local = unpruned_pairs[0]
        pruned_global = get_symmetry_pairs_from_symmetric_vertices(source_character, bs_diffs, vertex_activation_all)

        # print("unpruned pairs: ", str([ep_utils.fix_indices_for_zero_blendshapes(i) for i in unpruned_pairs[0]]), str([ep_utils.fix_indices_for_zero_blendshapes(i) for i in unpruned_pairs[1]])) # THIS IS 2 LISTS, LOCAL AND GLOBAL
        # then, we want to ensure each blendshape only occurs in ONE symmetry pair for both local and global (i.e. we can have local pair [0,1] and global pair [0,2], but not two local pairs [0,1], [1,3])
        # we ALSO want to take into account that we can't create chains... this will be awkward. find [a,b], next list, find [a,c], [b,d] if and only if c does not exist in first list.
        #   - mark which elements are chosen in first list (let's do global first... is more important)
        #   - once you encounter element in second list, if wasn't in first then fine, however if it was, only accept if the pair elements are also a pair
        return_pairs = []

        chosen_indices_global = []
        for pair in pruned_global:
            for item in pair:
                if item not in chosen_indices_global:
                    chosen_indices_global.append(item)

        pruned_local = []
        chosen_indices_local = []

        # idk man why not
        next_pair_must_be_shared = [] # list of pairs who must share their next pair to comlpete the cycle i.e. [a,b] and [b,c] have been found, we add [a,c] to this list, when we find [a,d] we define [c,d] to close the loop

        for pair in unpruned_pairs[0]:
            if pair[0] not in chosen_indices_local and pair[1] not in chosen_indices_local:

                # covering the next pair must be shared
                for i in next_pair_must_be_shared:
                    if pair[0] in i:
                        # need to add 2 symmetries to close loop
                        chosen_indices_local.append(i[0])
                        chosen_indices_local.append(i[1])
                        chosen_indices_local.append(pair[1])
                        pruned_local.append([i[0], pair[1]])
                        pruned_local.append([i[1], pair[1]])
                        # print("adding ", [i[0], pair[1]])
                        # print("adding ", [i[1], pair[1]])
                    elif pair[1] in i:
                        # need to add 2 symmetries to close loop
                        chosen_indices_local.append(i[0])
                        chosen_indices_local.append(i[1])
                        chosen_indices_local.append(pair[0])
                        pruned_local.append([i[0], pair[0]])
                        pruned_local.append([i[1], pair[0]])
                        # print("adding ", [i[0], pair[0]])
                        # print("adding ", [i[1], pair[0]])
                    next_pair_must_be_shared.remove(i)
                    break

                # CASE: no symmetry pairs with these indices exist, no chance of causing loops
                if pair[0] not in chosen_indices_global and pair[1] not in chosen_indices_global:
                    chosen_indices_local.append(pair[0])
                    chosen_indices_local.append(pair[1])
                    pruned_local.append(pair)
                    # print("adding ", pair)

                else:
                    pair_0_global = [i for i in pruned_global if pair[0] in i]
                    if len(pair_0_global) > 0:
                        pair_0_global = pair_0_global[0]
                    pair_1_global = [i for i in pruned_global if pair[1] in i]
                    if len(pair_1_global) > 0:
                        pair_1_global = pair_1_global[0]


                    # CASE: THIS BIT, NEED TO ADD WHAT TO DO WHEN I HAVE AN a->b->c CHAIN AND CAN STILL POSSIBLY FIND A D LOL
                    if len(pair_0_global) == 0 or len(pair_1_global) == 0:
                        chosen_indices_local.append(pair[0])
                        chosen_indices_local.append(pair[1])
                        pruned_local.append(pair)
                        # print("adding ", pair)

                        if len(pair_0_global) == 0:
                            items = [i for i in pair_1_global if i not in pair]
                            items.append(pair[0])
                            next_pair_must_be_shared.append(items)

                        if len(pair_1_global) == 0:
                            items = [i for i in pair_0_global if i not in pair]
                            items.append(pair[1])
                            next_pair_must_be_shared.append(items)


                    # CASE: both indices have symmetry pairs already, close the loop
                    else:
                        items = []
                        items.extend(pair_0_global)
                        items.extend(pair_1_global)
                        for i in pair:
                            if i in items:
                                items.remove(i)
                        items.sort()
                        # if items in pruned_global or len([i for i in items if i in chosen_indices_global]):#(items[0] not in chosen_indices_global and items[1] not in chosen_indices_global):
                        chosen_indices_local.append(pair[0])
                        chosen_indices_local.append(pair[1])
                        pruned_local.append(pair)
                        # print("adding ", pair)
                        chosen_indices_local.append(items[0])
                        chosen_indices_local.append(items[1])
                        pruned_local.append(items)
                        # print("adding ", items)

        return_pairs = pruned_local + pruned_global


    # print("remaining pairs: " + str([ep_utils.fix_indices_for_zero_blendshapes(i) for i in return_pairs]))
    return return_pairs



def get_symmetry_pairs_multiple(symmetry_groups, bs_displacements):
    local_symmetry_pairs = []
    global_symmetry_pairs = []
    symmetry_pairs = []

    # check each blendshape
    for index in range(len(bs_displacements)):    
        # check local groups first
        axis = [1,0,0]
        not_axis = [1,-1,1]

        local_symmetry = find_all_symmetric_blendshape(index, bs_displacements, symmetry_groups[:6], axis, not_axis) # this now returns tuple (dot_prod, blendshape_index)
        for (dot_prod, symmetric_blendshape) in local_symmetry:
            pair = [index, symmetric_blendshape]
            # print("local: " + str(pair))
            pair.sort()
            if pair not in symmetry_pairs:
                symmetry_pairs.append(pair)
                local_symmetry_pairs.append((dot_prod, pair))

        axis = [0,1,0]
        not_axis = [-1,1,1]

        global_symmetry = find_all_symmetric_blendshape(index, bs_displacements, symmetry_groups[6:8], axis, not_axis)
        for (dot_prod, symmetric_blendshape) in global_symmetry:
            pair = [index, symmetric_blendshape]
            # print("global: " + str(pair))
            pair.sort()
            if pair not in symmetry_pairs:
                symmetry_pairs.append(pair)
                global_symmetry_pairs.append((dot_prod, pair))

    # order blendshapes by symmetry
    local_symmetry_pairs.sort()
    global_symmetry_pairs.sort()
    local_symmetry_pairs.reverse()
    global_symmetry_pairs.reverse()


    # strip dot product as we only want blendshapes
    local_stripped = [j for (i,j) in local_symmetry_pairs]
    global_stripped = [j for (i,j) in global_symmetry_pairs]

    return [local_stripped, global_stripped]


def import_symmetric_vertices(file):
    sym_verts = []
    with open(file, "rb") as f:
        sym_verts = pickle.load(f)
    return sym_verts

def get_symmetric_vertices_path(character):
    if character in ["mateo", 'louise', 'louise_tatiana_cor', 'macaw', 'macaw_dwarf_dissimilar', 'tatiana', 'tatiana_reduced', 'louise_elf_dissimilar', 'new_elf', 'new_dwarf']:
        return './meshes/' + character + '/symmetric_vertex_pairs.txt'
    if character == "mateo_06":
        return './meshes/mateo/symmetric_vertex_pairs.txt'
    else:
        print("No symmetric vertices defined for character: " + character)
        exit(1)

def get_symmetry_pairs_from_symmetric_vertices(character, delta_blendshapes, vertex_activation):
    sym_verts = import_symmetric_vertices(get_symmetric_vertices_path(character))
    left_verts = sym_verts[0]
    right_verts = sym_verts[1]

    print("detecting symmetry for " + character)

    # LOUISE
    self_error = 0.4 # lower means more blendshapes will be considered symmetric
    # error = 0.9 # higher means more symmetric pairs will be found # I now define this as a relative measure, see below

    # TATIANA
    #self_error = 0.99

    # check if symmetric with self
    symmetric_blendshapes = []
    for i in range(len(delta_blendshapes)):

        vertex_activation_inv = np.array([0] * len(vertex_activation[i]))
        vertex_activation_inv[left_verts] = vertex_activation[i][right_verts]
        vertex_activation_inv[right_verts] = vertex_activation[i][left_verts]

        diff = sum(vertex_activation[i] & vertex_activation_inv)/sum(vertex_activation[i] | vertex_activation_inv)
        # print(i, diff)

        if (diff > self_error):
            # print(str(ep_utils.fix_indices_for_zero_blendshapes([i])) + " with diff " + str(diff))
            symmetric_blendshapes.append(i)
        # else:
        #     print("NO " + str(ep_utils.fix_indices_for_zero_blendshapes([i])) + " with diff " + str(diff))

    # print("symmetric blendshapes, won't be included for pair checks: " + str(symmetric_blendshapes))

    symmetric_blendshape_pairs = []
    chosen_blendshapes = []

    for i in range(len(delta_blendshapes)):
        if i not in symmetric_blendshapes and i not in chosen_blendshapes:
            print("checking " + str(i))

            potential_pairs = []

            for j in range(len(delta_blendshapes))[i+1:]:

                vertex_activation_inv_j = np.array([0] * len(vertex_activation[j]))
                vertex_activation_inv_j[left_verts] = vertex_activation[j][right_verts]
                vertex_activation_inv_j[right_verts] = vertex_activation[j][left_verts]

                if j not in symmetric_blendshapes and j not in chosen_blendshapes and sum(vertex_activation[i] & vertex_activation_inv_j) > 0:
                    bs_inv = np.array(delta_blendshapes[j])*[-1,1,1]


                    # only take active areas NEED TO DO BEFORE GETTING DIFFERENCE
                    delta_bs_active = np.array([a*np.array(([b]*3)) for (a,b) in zip(delta_blendshapes[i], vertex_activation[i])])
                    bs_inv_active = np.array([a*np.array(([b]*3)) for (a,b) in zip(bs_inv, vertex_activation[j])])
                    delta_bs_active[left_verts] -= bs_inv_active[right_verts]
                    delta_bs_active[right_verts] -= bs_inv_active[left_verts]
                    diff = sum(np.linalg.norm(i)**2 for i in delta_bs_active)

                    diff /= sum(vertex_activation[i] & vertex_activation_inv_j)


                    error = 0.4*min(max([np.linalg.norm(a) for a in delta_blendshapes[i]]),max([np.linalg.norm(a) for a in delta_blendshapes[j]]))
                    if (diff < error):
                        potential_pairs.append([diff, j])

            if len(potential_pairs) > 0:
                potential_pairs.sort()
                best_match = potential_pairs[0][1]
                symmetric_blendshape_pairs.append([i,best_match])
                chosen_blendshapes.append(best_match)

    # print("symmetric pairs: " + str(symmetric_blendshape_pairs))
    return symmetric_blendshape_pairs


def remove_overlap_for_pairs(vertex_activation_all, symmetry_pairs):
    for pair in symmetry_pairs:
        for i in range(len(vertex_activation_all[0])):
            if vertex_activation_all[pair[0]][i] == 1 and vertex_activation_all[pair[1]][i] == 1:
                vertex_activation_all[pair[1]][i] = 0

    return vertex_activation_all

def identify_overlap_groups(pairs):
    groups = []
    for pair in pairs:
        found = False
        for group in groups:
            if pair[0] in group or pair[1] in group:
                # print("extending group", group)
                group.extend(pair)
                found = True
                break
        if not found:
            # print("creating group", pair)
            groups.append(pair)

    # print("groups", groups)
    groups = [list(set(group)) for group in groups]
    # print("groups cleaned", groups)

    # returning redundant pairs for the overlap calculation
    redundant_pairs = []
    for group in groups:
        for i in range(len(group)-1):
            for j in range(i+1,len(group)):
                redundant_pairs.append([group[i],group[j]])

    return redundant_pairs