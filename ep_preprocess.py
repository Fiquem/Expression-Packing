import numpy as np

### PREPROCESSING

## BINARY VERTEX DISPLACEMENT VECTOR
# create activation array, 1 if vertex moves from neutral position, 0 is same (with lenience)
# scale everything to unit height cube ? so that the threshold is size-invariant, DO UNIFORM SCALING

# need min,max for x,y,z - find biggest diff + return. divide all by that to scale everything to unit cube.
def get_mins_maxs_xyz(blendshape):
    mins = np.copy(blendshape[0])
    maxs = np.copy(blendshape[0])
    for coord in blendshape[1:]:
        if coord[0] < mins[0]:
            mins[0] = coord[0]
        if coord[0] > maxs[0]:
            maxs[0] = coord[0]
        if coord[1] < mins[1]:
            mins[1] = coord[1]
        if coord[1] > maxs[1]:
            maxs[1] = coord[1]
        if coord[2] < mins[2]:
            mins[2] = coord[2]
        if coord[2] > maxs[2]:
            maxs[2] = coord[2]
    return (mins,maxs)

def get_largest_axis_length(blendshape):
    (mins,maxs) = get_mins_maxs_xyz(blendshape)
    diffs = maxs-mins
    max_diff = max(diffs)
    return max_diff

def calculate_binary_vertex_displacement_vector(neutral, blendshapes, method='error', threshold=0.0):
    vertex_activation_all = []
    
    # this method is absolute and NOT GOOD
    if method == 'error':
        # threshold_decimal_places = 2
        shape_threshhold = threshold # default 0.001
        largest_length = get_largest_axis_length(neutral)
        neutral_shape = neutral/largest_length
        for shape in blendshapes:
            largest_length = get_largest_axis_length(shape)
            shape = shape/largest_length
            vertex_activation = []
            vertex_count = 0
            for vertex in shape:
                vertex_diff = vertex - neutral_shape[vertex_count]
                vertex_diff_mag = np.linalg.norm(vertex_diff)
                if vertex_diff_mag < shape_threshhold:
                # if round(vertex[0], threshold_decimal_places) == round(neutral_shape[vertex_count][0], threshold_decimal_places) and round(vertex[1], threshold_decimal_places) == round(neutral_shape[vertex_count][1], threshold_decimal_places) and round(vertex[2], threshold_decimal_places) == round(neutral_shape[vertex_count][2], threshold_decimal_places):
                    vertex_activation += [0]
                else:
                    vertex_activation += [1]
                vertex_count += 1
            vertex_activation_all.append(vertex_activation)
        vertex_activation_all = np.array(vertex_activation_all)

    # I think this should be done with standard deviations? or means? rather than max?
    elif method == 'displacement percentage':
        displacement_percentage = threshold # default 0.2
        for i in range(len(blendshapes)):

            # calculate max displacement
            magnitudes = []
            for j in range(len(blendshapes[0])):
                magnitudes.append(np.linalg.norm(blendshapes[i][j] - neutral[j]))
            displacement = max(magnitudes)

            shape_threshhold = displacement*displacement_percentage
            vertex_activation = []
            vertex_count = 0
            for vertex in blendshapes[i]:
                vertex_diff = vertex - neutral[vertex_count]
                vertex_diff_mag = np.linalg.norm(vertex_diff)
                if vertex_diff_mag < shape_threshhold:
                    vertex_activation += [0]
                else:
                    vertex_activation += [1]
                vertex_count += 1
            vertex_activation_all.append(vertex_activation)
        vertex_activation_all = np.array(vertex_activation_all)

    elif method == 'bounding box':
        print("calculating vertex activation")
        # get diagonal for each shape
        for shape in blendshapes:
            (mins,maxs) = get_mins_maxs_xyz(shape) # this is stupid since the mesh almost never changes
            print(mins,maxs)
            diagonal = np.linalg.norm(maxs-mins)
            shape_threshhold = diagonal*threshold #0.004 necessary for macaw I think! 0.007 too large for mateo (defaults 0.004, 0.005 (I think!))
            vertex_activation = []
            vertex_count = 0
            for vertex in shape:
                vertex_diff = vertex - neutral[vertex_count]
                vertex_diff_mag = np.linalg.norm(vertex_diff)
                if vertex_diff_mag < shape_threshhold:
                # if round(vertex[0], threshold_decimal_places) == round(neutral_shape[vertex_count][0], threshold_decimal_places) and round(vertex[1], threshold_decimal_places) == round(neutral_shape[vertex_count][1], threshold_decimal_places) and round(vertex[2], threshold_decimal_places) == round(neutral_shape[vertex_count][2], threshold_decimal_places):
                    vertex_activation += [0]
                else:
                    vertex_activation += [1]
                vertex_count += 1
            vertex_activation_all.append(vertex_activation)
            # print(sum(vertex_activation))
        vertex_activation_all = np.array(vertex_activation_all)

    else:
        print(method + " is an undefined method.")
        exit(1)

    # if any blendshape has a zero activation, break
    for bs in vertex_activation_all:
        if sum(bs) == 0:
            print("With the vertex activation method " + method + " and current shape threshold " + str(threshold) + ", there is a blendshape with zero activation.")
            exit(1)

    return vertex_activation_all

## BLENDSHAPE SIMILARITY MATRIX
# function to return blendshape similarity as given in J.P. Lewis paper Practice and Theory of Blendshape Facial Models
# Figure 12
# b_i^T * b_j / || b_i || || b_j ||
# the result is between -1 and 1 as it takes direction into account. we can abs() the result as we only care about difference, not direction
def get_Pearson_correlation_coefficient(bs1, bs2):
    bs1 = np.matrix(bs1)
    bs2 = np.matrix(bs2)
    # print("top: " + str((bs1 * bs2.transpose())))
    # print("bot: " + str(np.linalg.norm(bs1) * np.linalg.norm(bs2)))
    if (np.linalg.norm(bs1) * np.linalg.norm(bs2)) == 0:
        return 0.0
    else:
        return (bs1 * bs2.transpose()) / (np.linalg.norm(bs1) * np.linalg.norm(bs2))

# calculates similarity purely from dot product
def get_dot_product_between_blendshapes(bs1,bs2):
    bs1 = np.matrix(bs1)
    bs2 = np.matrix(bs2)
    return np.dot(bs1,bs2.transpose())

# get bs difference from neutral
def get_difference_vector(neutral, blendshapes):
    bs_diff = []
    for i in range(len(blendshapes)):
        bs_diff.append(blendshapes[i] - neutral)
    return bs_diff

# create mutual coherence/blendshape similarity matrix
def create_similarity_matrix(blendshape_deltas, method):
    bs_diff = blendshape_deltas
    similarity_matrix = np.zeros((len(bs_diff),len(bs_diff)))

    if method == 'Pearson':
        for i in range(len(bs_diff)):
            for j in range(len(bs_diff)):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    similarity_matrix[i][j] = max(get_Pearson_correlation_coefficient(bs_diff[i].flatten(),bs_diff[j].flatten()), 0)

    # elif method == 'dot':
    #     for i in range(len(bs_diff)):
    #         for j in range(len(bs_diff)):
    #             if i == j:
    #                 similarity_matrix[i][j] = 0.0
    #             else:
    #                 similarity_matrix[i][j] = get_dot_product_between_blendshapes(bs_diff[i].flatten(),bs_diff[j].flatten())

    else:
        print("Similarity matrix method \"" + str(method) + "\" undefined.")
        exit(1)

    return similarity_matrix


# ORIGINAL
def get_blendshape_uniqueness(sim_matrix):
    uniquenesses = []
    for i in range(len(sim_matrix)):
        row = sim_matrix[i]
        uniquenesses.append((sum(row) - row[i])/(len(row) - 1))
    return np.array(uniquenesses)


## VERTEX DISPLACEMENT
# just get biggest vertex displacement
def get_blendshape_displacement(blendshape_deltas, blendshape_activation, method):
    displacement = []
    bs_diff = blendshape_deltas

    # only count active vertices
    bs_diff = np.array([[blendshape_activation[i][j] * bs_diff[i][j] for j in range(len(bs_diff[0]))] for i in range(len(bs_diff))])

    if method == 'max': # calculate largest single vertex displacement
        displacement = []
        for i in range(len(bs_diff)):
            magnitudes = []
            for j in range(len(bs_diff[0])):
                magnitudes.append(np.linalg.norm(bs_diff[i][j]))
            displacement.append(max(magnitudes))
    elif method == 'sum': # calculate sum of all displacements
        displacement = []
        for i in range(len(bs_diff)):
            magnitudes = []
            for j in range(len(bs_diff[0])):
                magnitudes.append(np.linalg.norm(bs_diff[i][j]))
            displacement.append(sum(magnitudes))
    elif method == 'avg': # calculate avg of all displacements
        displacement = []
        for i in range(len(bs_diff)):
            magnitudes = []
            for j in range(len(bs_diff[0])):
                magnitudes.append(np.linalg.norm(bs_diff[i][j]))
            displacement.append(sum(magnitudes)/sum(blendshape_activation[i]))

    # normalise
    # sum and avg end up the same after normalising
    displacement = (np.array(displacement) / max(displacement))
    # print(displacement)

    return displacement



##  NON-SIMILAR TRIANGLES
# takes into account the source AND target mesh
# calculates non-similarity metric between each triangle in source and target neutrals
# metric for each blendshape is then sum of triangles affected by blendshape
#
# s = max(BA_1/BA_2, BA_2/BA_1) + max(BC_1/BC_2, BC_2/BC_1)-2 (for ABC_1 and ABC_2, triangles in meshes 1 and 2)
# blendshape__triangle_weight = sum(s_i) for each triangle i that is moved by the blendshape
def special_max(vec0, vec1):
    # no idea what to do with these but let's just return things that make my code work for the moment
    if vec0 == 0 and vec1 == 0:
        # print("why is this in this mesh")
        return 1
    elif vec0 == 0:
        print("unsure what to do")
        return 2 - vec1
    elif vec1 == 0:
        print("unsure what to do")
        return 2 - vec0
    else:
        return max(vec0/vec1, vec1/vec0)


def get_similarity_of_triangles(source_triangles, source_neutral, target_triangles, target_neutral, vertex_activation):
    tri_diffs = []

    # DON'T HAVE MESHES WITH SIMILAR TOPOLOGY TO TEST WITH YET WHOOPS
    for (s_tri, t_tri) in zip(source_triangles, target_triangles):
        s_abc = np.array([source_neutral[s_tri[0]-1], source_neutral[s_tri[1]-1], source_neutral[s_tri[2]-1]])
        t_abc = np.array([target_neutral[t_tri[0]-1], target_neutral[t_tri[1]-1], target_neutral[t_tri[2]-1]])

        s_ba = np.linalg.norm(s_abc[0] - s_abc[1])
        s_bc = np.linalg.norm(s_abc[2] - s_abc[1])
        t_ba = np.linalg.norm(t_abc[0] - t_abc[1])
        t_bc = np.linalg.norm(t_abc[2] - t_abc[1])

        tri_diffs.append(special_max(s_ba, t_ba) + special_max(s_bc, t_bc) - 2)

    # size diff is due to one being a list of triangles and one being a list of vertices
    # need to loop through tris, if active vert in tri, add to BS sum
    # normalisation: max needs to be found before this point
    similarities = np.zeros(len(vertex_activation))

    for i in range(len(tri_diffs)):
        vertices_in_tri = source_triangles[i] # vertices_in_tri = [x,y,z] where these are indices of the vertices used
        diff = tri_diffs[i] # the amount to add to similarities[whatever_index] for each bs with an active vertex in vertices_in_tri

        for j in range(len(vertex_activation)):
            if vertex_activation[j][vertices_in_tri[0]-1] or vertex_activation[j][vertices_in_tri[1]-1] or vertex_activation[j][vertices_in_tri[2]-1]:
                similarities[j] += diff

    # might need this line when values aren't 0? Not sure
    # similarities = [similarities[i] / sum(vertex_activation[i]) for i in range(len(similarities))]

    if max(similarities) == 0:
        return np.array(similarities)
    else:
        return (np.array(similarities) / max(similarities))


# do I even need this? v similar to blendshape_displacement method
def get_vertex_displacement(active_verts, diffs, method='avg'):
    bs_disps = []

    for (diff,verts) in zip(diffs,active_verts):
        active_diff = [i*np.array(j) for (i,j) in zip(diff,verts)] # only take into account the active vertices

        if method == 'avg':
            avg = sum(active_diff)/sum(verts)
            bs_disps.append(avg)
            # bs_disps.append(avg/np.linalg.norm(avg))
        elif method == 'max':
            max_diff_mag = 0
            for i in range(len(active_diff)):
                if np.linalg.norm(active_diff[i]) > max_diff_mag:
                    max_diff = active_diff[i]
            bs_disps.append(max_diff)
            # bs_disps.append(max_diff/np.linalg.norm(max_diff))

    return(bs_disps)