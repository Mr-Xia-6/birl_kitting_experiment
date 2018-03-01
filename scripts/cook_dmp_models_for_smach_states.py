#!/usr/bin/env python
import numpy
import birl_baxter_dmp.dmp_train
from sklearn.externals import joblib
import os
import glob
import numpy
import birl_baxter_dmp.dmp_train
import birl_baxter_dmp.dmp_generalize
import ipdb
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import random

dir_of_this_script = os.path.dirname(os.path.realpath(__file__))
demonstrations_dir = os.path.join(dir_of_this_script, '..', 'data', 'demonstrations')
dmp_model_dir = os.path.join(dir_of_this_script, '..', 'data', 'dmp_models')
dmp_model_profiles = os.path.join(dir_of_this_script, '..', 'data', 'dmp_model_profiles')

def profile_dmp(list_of_mat, dmp_model, fname):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')  
    for mat in list_of_mat:
        ax.set_xlim3d(0, 2)
        ax.set_ylim3d(-2, 2)
        ax.set_zlim3d(-2, 2)
        ax.plot(mat[:, 0], mat[:, 1], mat[:, 2], color='black')

    for mat in list_of_mat:
        start = mat[0].copy()
        end = mat[-1].copy()
        gen_mat = birl_baxter_dmp.dmp_generalize.dmp_imitate(starting_pose=start, ending_pose=end, weight_mat=dmp_model["basis_weight"], base_fuc=dmp_model["basis_function_type"])
        ax.plot(gen_mat[:, 0], gen_mat[:, 1], gen_mat[:, 2], color='green')

    for mat in list_of_mat:
        for i in range(3):
            start = mat[0].copy()+numpy.random.normal(0,pow(0.1,i),mat.shape[1])
            end = mat[-1].copy()+numpy.random.normal(0,pow(0.1,i),mat.shape[1])
            gen_mat = birl_baxter_dmp.dmp_generalize.dmp_imitate(starting_pose=start, ending_pose=end, weight_mat=dmp_model["basis_weight"], base_fuc=dmp_model["basis_function_type"])
            ax.plot(gen_mat[:, 0], gen_mat[:, 1], gen_mat[:, 2], color='red')

    ax.set_title(fname)
    fig.show()

def filter_static_points(mat):
    last = mat[0]
    new_mat = [last]
    for idx in range(mat.shape[0]):
        if numpy.linalg.norm(mat[idx]-last) < 0.01:
            pass
        else:
            new_mat.append(mat[idx])
            last = mat[idx] 

    return numpy.array(new_mat)


if __name__ == '__main__':
    d = {}
    for f in glob.glob(os.path.join(demonstrations_dir, '*.npy')):
        label = os.path.basename(f)[:-4].split('.')[0]
        if label not in d:
            d[label] = []
        d[label].append(f)
    print d

    for label in d: 
        list_of_mat = [filter_static_points(numpy.load(f)) for f in d[label]]
        basis_weight, basis_function_type = birl_baxter_dmp.dmp_train.train(list_of_mat)
        model = {
            "basis_weight": basis_weight,
            "basis_function_type": basis_function_type,
        }
        if not os.path.isdir(dmp_model_dir):
            os.makedirs(dmp_model_dir)
        joblib.dump(
            model,
            os.path.join(dmp_model_dir, label)
        )

        profile_dmp(list_of_mat, model, label)
    
    raw_input()
