import numpy as np

def xy_euclidean_dist(a1, a2): 
    return ((a1[0] - a2[0]) ** 2 + (a1[1] - a2[1]) ** 2) ** 0.5 


def vectorize(u, v):
    assert(len(u) == len(v)) # cant vectorize unequal lengths
    return [v[i] - u[i] for i in range(len(v))]

def vector_magnitude(vector):
    return sum([dim**2 for dim in vector]) ** 0.5

def cos_angle(u, v):
    return np.dot(u, v) / (vector_magnitude(u) * vector_magnitude(v))