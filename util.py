import numpy as np

def xy_euclidean_dist(a1, a2): 
    return ((a1[0] - a2[0]) ** 2 + (a1[1] - a2[1]) ** 2) ** 0.5 

def clamp(value, lower_bound, upper_bound):
    return min(upper_bound, max(value, lower_bound))

def vectorize(u, v):
    assert(len(u) == len(v)) # cant vectorize unequal lengths
    return [v[i] - u[i] for i in range(len(v))]

def vector_magnitude(vector):
    return sum([dim**2 for dim in vector]) ** 0.5

def cos_angle(u, v):
    u_mag = vector_magnitude(u)
    v_mag = vector_magnitude(v)
    if (u_mag == 0 or v_mag == 0):
        return 0
    return np.dot(u, v) / (vector_magnitude(u) * vector_magnitude(v))
