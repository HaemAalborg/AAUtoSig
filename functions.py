import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.spatial as sp
from itertools import permutations


def plotsigs(context, mutation, intensities):
    colors = {'C>A': 'r', 'C>G': 'b', 'C>T': 'g', 
              'T>A' : 'y', 'T>C': 'c','T>G' : 'm' }
    plt.figure(figsize=(20,7))
    plt.bar(x = context, 
            height =  intensities/np.sum(intensities), 
            color = [colors[i] for i in mutation])
    labels = list(colors.keys())
    handles = [plt.Rectangle((0,0),1,1, color=colors[label]) for label in labels]
    plt.legend(handles,labels)
    plt.xticks(rotation=90)
    


#This function takes to matrices of equal size, calculates the row-wise cosine
#similarity between the two matrices and permutes the rows to have the highest
#possible diagonal values. 
#It returns the permuted cosine matrix, and the arrangement of matrix B's rows
#that generates the highest cosine similarity with the corresponding rows in A
A = np.random.rand(3,2)
B = np.random.rand(3,2)
def cosine_perm(A,B):
    def acc(x):
        return(np.sum(np.diag(x)))
    #This operation creates the cosine distance matrix between rows in A and rows 
    #in B, where the rows in sim represent the rows in A and the columns in sim 
    #represent the rows in B.
    sim = 1 - sp.distance.cdist(A, B, 'cosine')
    curr_x = acc(sim)
    best_pe = sim
    best_idx =range(A.shape[0])
    for pe, idx in zip(permutations(sim), permutations(best_idx)):
        pe = np.array(pe)
        if(acc(pe)>curr_x):
            curr_x = acc(pe)
            best_pe = pe
            best_idx = idx
            
    return((best_pe, best_idx))