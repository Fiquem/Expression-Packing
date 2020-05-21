import numpy as np
import pulp
import cvxpy
import ep_preprocess
import ep_utils
import ep_symmetry
# import matplotlib.pyplot as plt
from datetime import datetime
import os

one_loop_time = 0

### METHODS

def update_blendshape_uniqueness_weights(blendshape_uniquenesses, blendshape_indices, similarity_matrix):
    new_uniquenesses = []
    for i in range(len(blendshape_uniquenesses)):
        new_uniqueness = blendshape_uniquenesses[i]
        for b in blendshape_indices:
            new_uniqueness *= 1.0-similarity_matrix[i][b]
        new_uniquenesses.append(new_uniqueness)

    return new_uniquenesses

def get_bs_largest_activation(bs, indices):
    largest_bs_sum = 0
    largest_bs_index = 0
    for i in indices:
        current_bs_sum = sum(bs[i])
        if current_bs_sum > largest_bs_sum:
            largest_bs_sum = current_bs_sum
            largest_bs_index = i
    return largest_bs_index

def get_bs_smallest_activation(bs, indices):
    smallest_bs_sum = 999999
    smallest_bs_index = 0
    for i in indices:
        current_bs_sum = sum(bs[i])
        if current_bs_sum < smallest_bs_sum:
            smallest_bs_sum = current_bs_sum
            smallest_bs_index = i
    return smallest_bs_index

def remove_overlapping_bs(bs_activation, indices, index, threshold):
    comparison_bs = np.array(bs_activation[index])
    comparison_bs_sum = sum(comparison_bs)
    if index in indices: # need to check as we now check for symmetry before removal, which makes things messy
        indices.remove(index)
    temp_indices = indices.copy()
    for i in indices:
        if sum(comparison_bs & bs_activation[i]) > threshold*0.5*(sum(comparison_bs) + sum(bs_activation[i])):
                temp_indices.remove(i)
    return temp_indices

def append_blendshape_user_input(result_blendshapes, new_blendshape, vertex_activation_all, current_indices):

    overlap_threshold = 0
    user_input = ""

    while user_input != "y" and user_input != "n":
        user_input = input("Would you like to add blendshape " + str(new_blendshape) + " (y/n):   ")

    if user_input == "y":
        print("Including " + str(new_blendshape))
        result_blendshapes.append(new_blendshape)
        current_indices = remove_overlapping_bs(vertex_activation_all, current_indices, new_blendshape, overlap_threshold)
    else:
        print("Blendshape " + str(new_blendshape) + " will not be included")
        if new_blendshape in current_indices:
            current_indices.remove(new_blendshape)

    return (result_blendshapes, current_indices)



def set_packing_greedy(vertex_activation_all, importance_weights, similarity_matrix, symmetry_pairs, displacements, blendshape_uniquenesses, triangle_similarities):
    ## GREEDY SET PACKING APPROXIMATION
    # For Set Packing, we describe an analogous algorithm that greedily selects additional sets until no more
    # can be added. For convenience, we describe the weights somewhat differently than in the above. Let
    # the input be a set of input set names I, each of the sets Si for i ∈ I, and weights given by ci ∈ R+ for
    # i ∈ I

    # H ← ∅
    # while I != ∅ do
    #     b ← argmax_(i∈I) (√c_i)/|Si|         # Here we can use c_i^2/|Si| instead for the same results.
    #     H ← H ∪ {b}
    #     for all i ∈ I do
    #         if Si ∩ Sb != ∅ then
    #             I ← I − i
    #         end if
    #     end for
    # end while
    # return H

    # H = result set/blendshapes names/numbers
    # I = all sets/blendshapes
    # S_i = ith element of I
    # c_i = weight/cost of S_i (what does this mean???? easier for me bc all weights are 1 so I just take largest?)

    all_results = []

    importance_weights = [(2.0-i) for i in importance_weights] # THIS IS VERY IMPORTANT
    #blendshape_uniquenesses = [i*-1 for i in blendshape_uniquenesses]

    current_importance_weights = importance_weights.copy()
    current_blendshape_uniquenesses = blendshape_uniquenesses.copy()

    overlap_threshold = 0

    one_loop = True

    all_indices = list(range(len(vertex_activation_all)))
    while len(all_indices) != 0:# and min(current_blendshape_uniquenesses) < -0.01:
        # print(min(current_blendshape_uniquenesses))

        oneLoopStartTime = datetime.now()
        result_blendshapes = []
        current_indices = all_indices.copy()
        blendshapes_to_update_uniqueness = []
        while len(current_indices) != 0:

            if len(importance_weights) == 0:
                # with no importance weights
                next_bs = get_bs_smallest_activation(vertex_activation_all, current_indices)
            else:
                # with weights
                next_bs = get_bs_smallest_activation([current_importance_weights[i]*vertex_activation_all[i] for i in range(len(vertex_activation_all))], current_indices)

            # check for symmetry
            symmetric_blendshapes = []
            # symmetric_blendshapes = ep_symmetry.find_symmetric_blendshapes_from_pairs(next_bs, symmetry_pairs, current_indices)
            # print("Adding symmetric blendshapes for " + str(next_bs) + ": " + str(symmetric_blendshapes))

            # append results
            for bs in [next_bs] + symmetric_blendshapes:
                # (result_blendshapes, current_indices) = append_blendshape_user_input(result_blendshapes, bs, vertex_activation_all, current_indices)
                result_blendshapes.append(bs)
                current_indices = remove_overlapping_bs(vertex_activation_all, current_indices, bs, overlap_threshold)

        # COMMENTING OUT BLENDSHAPE UNIQUENESS FOR THE MOMENT
        #current_blendshape_uniquenesses = update_blendshape_uniqueness_weights(current_blendshape_uniquenesses, result_blendshapes, similarity_matrix)
        # print("bs uniquenesses (similarities) of selected blendshapes blendshapes: " + str(result_blendshapes))
        # if len(all_results) > 1:
        #     for bs in result_blendshapes:
        #         # print(bs, similarity_matrix[bs][0:bs] + similarity_matrix[bs][bs+1:])
        #         print("bs ", bs, " uniqueness MAX: ", max(list(similarity_matrix[bs][[i for j in all_results for i in j]])))
        #         print("bs ", bs, " uniqueness MAX POSSIBLE: ", max(list(similarity_matrix[bs][0:bs]) + list(similarity_matrix[bs][bs+1:])))
        #current_importance_weights = -1*(displacements + current_blendshape_uniquenesses + triangle_similarities)

        all_results.append(result_blendshapes)
        # print(sum(sum(vertex_activation_all[result_blendshapes])))
        for i in result_blendshapes:
            if i in all_indices:
                all_indices.remove(i)

        print("Results " + str(len(all_results)-1) + ": " + str(ep_utils.get_blendshapes_to_print(result_blendshapes)))
        print("Blendshapes covered: " + str(len(vertex_activation_all)-len(all_indices)))


        if one_loop:
            end_one_iter_solve_time = datetime.now()
            one_loop_time = end_one_iter_solve_time - oneLoopStartTime
            print("One loop execution time: " + str(one_loop_time))
            one_loop = False


    print("First loop time: ", one_loop_time)
    return all_results



def set_packing(vertex_activation_all, importance_weights, similarity_matrix, symmetry_pairs, displacements, blendshape_uniquenesses, triangle_similarities):
    ## SET PACKING
    # maximize the total number of subsets
    # subject to selected sets have to be pairwise disjoint
    # every set is either in the set packing or not

    w_vars = []
    var_num = 0
    for bs in vertex_activation_all:
        w_vars.append(pulp.LpVariable('w' + str(var_num).zfill(3), lowBound=0, upBound=1, cat='Integer'))
        var_num += 1

    # print("initial_importance_weights: " + str(importance_weights))
    current_importance_weights = importance_weights.copy()
    current_blendshape_uniquenesses = blendshape_uniquenesses.copy()

    all_results = []
    all_indices = list(range(len(vertex_activation_all)))
    all_pairs = symmetry_pairs.copy()
    do_symmetry = True

    one_loop = True

    while len(all_indices) != 0:
        oneLoopStartTime = datetime.now()
        my_lp_problem = pulp.LpProblem("My LP Problem", pulp.LpMaximize)

        if len(importance_weights) == 0:
            my_lp_problem += pulp.lpSum(w_vars)
        else:
            my_lp_problem += pulp.lpSum(np.array(current_importance_weights) * w_vars)

        # constraintsStartTime = datetime.now()
        for i in range(len(vertex_activation_all[0])):
            vertex_sum = 0
            for j in all_indices:
                vertex_sum += w_vars[j]*vertex_activation_all[j][i]
            my_lp_problem += pulp.lpSum(vertex_sum) <= 1
        # constraintsEndTime = datetime.now()
        # print("add constraints time: " + str(constraintsEndTime - constraintsStartTime))

        # eventually symmetry will cause empty result sets, so in that case no longer take symmetry into account
        if do_symmetry:
            # print("remaining blendshapes: " + str(all_indices))
            # print("pairs: " + str(all_pairs))
            for pair in all_pairs:
                my_lp_problem += w_vars[pair[0]] - w_vars[pair[1]] == 0

        # print(my_lp_problem)
        my_lp_problem.solve(pulp.CPLEX_CMD(msg = 1, options = ['set emphasis mip 4']))
        oneLoopEndTime = datetime.now()
        if one_loop:
            end_one_iter_solve_time = datetime.now()
            one_loop_time = end_one_iter_solve_time - oneLoopStartTime
            print("One loop execution time: " + str(one_loop_time))
            one_loop = False
        # print("solved status: " + str(pulp.LpStatus[my_lp_problem.status]))


        # for variable in my_lp_problem.variables():
        #     if variable.varValue == 1:
        #         print("{} = {}".format(variable.name, variable.varValue))

        result_sum = 0
        result_blendshapes = []
        for w in my_lp_problem.variables():
            if w.varValue == 1:
                i = int(w.name[1:])
                w_vars[i] = 0
                # print("removing " + str(i))
                result_blendshapes.append(i)
                all_indices.remove(i)
                for pair in all_pairs:
                    if i in pair:
                        all_pairs.remove(pair)
                result_sum += sum(vertex_activation_all[i])
        # result_blendshapes_to_print = ep_utils.fix_indices_for_zero_blendshapes(result_blendshapes)
        result_blendshapes_to_print = result_blendshapes
        print(result_blendshapes_to_print)
        # print(result_blendshapes)
        if len(result_blendshapes) == 0:
            print("remaining blendshapes: ", ep_utils.get_blendshapes_to_print(all_indices))
            print("remaining pairs", [ep_utils.get_blendshapes_to_print(i) for i in all_pairs])
            do_symmetry = False
        else:            
            all_results.append(result_blendshapes)
        # print(result_sum)

        # COMMENTING OUT BLENDSHAPE UNIQUENESS FOR THE MOMENT
        # current_blendshape_uniquenesses = update_blendshape_uniqueness_weights(current_blendshape_uniquenesses, result_blendshapes, similarity_matrix)
        # current_importance_weights = displacements + current_blendshape_uniquenesses + triangle_similarities

        # print(pulp.value(my_lp_problem.objective))

    print("First loop time: ", one_loop_time)
    return all_results

# stuff to run always here such as class/def
def main():
    startTime = datetime.now()

    # pulp.pulpTestAll()

    # load data
    source_character = 'louise'
    target_character = 'new_elf'
    expression_save_folder = './training_expressions/'

    print("loading source")
    (source_neutral, source_blendshapes) = ep_utils.load_mesh(source_character)
    print("loading target")
    target_neutral = ep_utils.load_mesh(target_character,target=True)

    source_triangles = ep_utils.load_mesh(source_character,target=False,triangles=True)
    target_triangles = ep_utils.load_mesh(target_character,target=True,triangles=True)

    # preprocess
    vertex_activation_all = ep_preprocess.calculate_binary_vertex_displacement_vector(source_neutral, source_blendshapes, 'displacement percentage', 0.3)
    bs_diffs = ep_preprocess.get_difference_vector(source_neutral, source_blendshapes)

    # get importance factor
    similarity_matrix = ep_preprocess.create_similarity_matrix(bs_diffs, 'Pearson')
    blendshape_uniquenesses = ep_preprocess.get_blendshape_uniqueness(similarity_matrix)
    displacements = ep_preprocess.get_blendshape_displacement(bs_diffs, vertex_activation_all, 'avg')
    triangle_similarities = ep_preprocess.get_similarity_of_triangles(source_triangles, source_neutral, target_triangles, target_neutral, vertex_activation_all)

    displacements = 0.5*displacements
    triangle_similarities = 0.5*triangle_similarities
    initial_importance_weights = displacements + triangle_similarities
    # blendshape_uniquenesses = 0.5*blendshape_uniquenesses
    # initial_importance_weights = displacements + triangle_similarities + blendshape_uniquenesses

    # plt.ion()
    # plt.imshow(similarity_matrix, cmap='gray', interpolation='none')
    # plt.pause(10)


    # BEGIN SYMMETRY COMMENT
    # identify symmetry groups
    symmetry_groups = ep_symmetry.find_blendshapes_in_symmetry_groups(source_character, vertex_activation_all)
    print("sym groups: " + str([ep_utils.get_blendshapes_to_print(i, source_character) for i in symmetry_groups]))
    # symmetry_groups = [[],[],[],[],[],[],[],[]]
    bs_disps = ep_preprocess.get_vertex_displacement(vertex_activation_all, bs_diffs, 'avg')

    # identify symmetry pairs USING BOTH METHODS COMBINED
    symmetry_pairs = ep_symmetry.get_symmetry_pairs(symmetry_groups, bs_disps, source_character, bs_diffs, vertex_activation_all) # use this one for BOTH NOW
    print("Symmetry Pairs: " + str([ep_utils.get_blendshapes_to_print(i) for i in symmetry_pairs]))

    # identify groups of pairs and remove overlaps there
    redundant_pairs = ep_symmetry.identify_overlap_groups(symmetry_pairs)
    vertex_activation_all = ep_symmetry.remove_overlap_for_pairs(vertex_activation_all, redundant_pairs)
    # END SYMMETRY COMMENT

    # TIMING START
    begin_solve_time = datetime.now()

    # FOR TESTING
    # SET ALL IMPORTANCE  TO 1
    # initial_importance_weights = np.ones(len(displacements))
    # SET NO SYMMETRY
    # symmetry_pairs = []


    # do method
    # resulting_expressions = set_packing_greedy(vertex_activation_all, initial_importance_weights, similarity_matrix, symmetry_pairs, displacements, blendshape_uniquenesses, triangle_similarities)
    resulting_expressions = set_packing(vertex_activation_all, initial_importance_weights, similarity_matrix, symmetry_pairs, displacements, blendshape_uniquenesses, triangle_similarities)
    print("Number results: " + str(len(resulting_expressions)))

    print("Full set of results:")
    #print([ep_utils.get_blendshapes_to_print(i, source_character) for i in resulting_expressions])
    resulting_expressions_to_print = [ep_utils.get_blendshapes_to_print(i, source_character) for i in resulting_expressions]
    print(resulting_expressions_to_print)

    # target_bs_diffs = ep_preprocess.get_difference_vector(source_neutral*np.array([1,1.0/0.6,1]), source_blendshapes*np.array([1,1.0/0.6,1]))

    # code for testing using meshes we already have blendshapes for
    # (_, target_blendshapes) = ep_utils.load_mesh(target_character)
    # target_bs_diffs = ep_preprocess.get_difference_vector(target_neutral, target_blendshapes)
    # ep_utils.save_expressions_obj(target_character, target_bs_diffs, resulting_expressions, expression_save_folder)

    # save config
    # ep_utils.create_ebfr_config_file('./',
    #     "example_based_v2", 
    #     ep_utils.get_neutral_obj_path(source_character), 
    #     ep_utils.get_neutral_obj_path(target_character, True), 
    #     ep_utils.get_blendshapes_folder(source_character),
    #     expression_save_folder,
    #     resulting_expressions_to_print,
    #     target_character + '_' + str(len(resulting_expressions_to_print)) + '_examples/',
    #     'config'
    #     )

    ep_utils.save_results_list(resulting_expressions_to_print)

    endTime = datetime.now()
    print("Execution time: " + str(endTime - startTime))

if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   main()