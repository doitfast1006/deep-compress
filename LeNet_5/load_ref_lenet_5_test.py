import os
import numpy as np
import pickle

file_pickle = './results_lenet_5/df_ref_lenet_5_pickle.pkl'
with open(file_pickle,'rb') as f:
	df_ref = pickle.load(f)

weights_pickle = './results_lenet_5/weights_biases_lenet_5_ref_pickle.pkl'

with open(weights_pickle,'rb') as f:
	w_bar = pickle.load(f)
	bias_bar = pickle.load(f)


import tensorflow as tf

import input_MNIST_data
from input_MNIST_data import shuffle_data
data = input_MNIST_data.read_data_sets("./data/", one_hot=True)

import numpy as np
import sys
import dill
import collections

import pickle

import pandas as pd

from sklearn.cluster import KMeans
from numpy import linalg as LA

print('----------------------------------------------')
print('architecture: LeNet-5 --- Data Set: MNIST')
print('----------------------------------------------')

# input and output shape
n_input   = data.train.images.shape[1]  # here MNIST data input (28,28)
n_classes = data.train.labels.shape[1]  # here MNIST (0-9 digits)

# dropout rate
dropout_rate = 0.5
# number of weights and bias in each layer
n_W = {}
n_b = {}

# network architecture hyper parameters
input_shape = [-1,28,28,1]
W0 = 28
H0 = 28

# Layer 1 -- conv
D1 = 1
F1 = 5
K1 = 20
S1 = 1
W1 = (W0 - F1) // S1 + 1
H1 = (H0 - F1) // S1 + 1
conv1_dim = [F1, F1, D1, K1]
conv1_strides = [1,S1,S1,1] 
n_W['conv1'] = F1 * F1 * D1 * K1
n_b['conv1'] = K1 

# Layer 2 -- max pool
D2 = K1
F2 = 2
K2 = D2
S2 = 2
W2 = (W1 - F2) // S2 + 1
H2 = (H1 - F2) // S2 + 1
layer2_ksize = [1,F2,F2,1]
layer2_strides = [1,S2,S2,1]

# Layer 3 -- conv
D3 = K2
F3 = 5
K3 = 50
S3 = 1
W3 = (W2 - F3) // S3 + 1
H3 = (H2 - F3) // S3 + 1
conv2_dim = [F3, F3, D3, K3]
conv2_strides = [1,S3,S3,1] 
n_W['conv2'] = F3 * F3 * D3 * K3
n_b['conv2'] = K3 

# Layer 4 -- max pool
D4 = K3
F4 = 2
K4 = D4
S4 = 2
W4 = (W3 - F4) // S4 + 1
H4 = (H3 - F4) // S4 + 1
layer4_ksize = [1,F4,F4,1]
layer4_strides = [1,S4,S4,1]


# Layer 5 -- fully connected
n_in_fc = W4 * H4 * D4
n_hidden = 500
fc_dim = [n_in_fc,n_hidden]
n_W['fc'] = n_in_fc * n_hidden
n_b['fc'] = n_hidden

# Layer 6 -- output
n_in_out = n_hidden
n_W['out'] = n_hidden * n_classes
n_b['out'] = n_classes

for key, value in n_W.items():
	n_W[key] = int(value)

for key, value in n_b.items():
	n_b[key] = int(value)

# tf Graph input
x = tf.placeholder("float", [None, n_input])
y = tf.placeholder("float", [None, n_classes])

learning_rate = tf.placeholder("float")
momentum_tf = tf.placeholder("float")
mu_tf = tf.placeholder("float")

# weights of LeNet-5 CNN -- tf tensors
weights = {
    # 5 x 5 convolution, 1 input image, 20 outputs
    'conv1': tf.get_variable('w_conv1', shape=[F1, F1, D1, K1],
           			initializer=tf.contrib.layers.xavier_initializer()),
    # 'conv1': tf.Variable(tf.random_normal([F1, F1, D1, K1])),
    # 5x5 conv, 20 inputs, 50 outputs 
    #'conv2': tf.Variable(tf.random_normal([F3, F3, D3, K3])),
    'conv2': tf.get_variable('w_conv2', shape=[F3, F3, D3, K3],
           			initializer=tf.contrib.layers.xavier_initializer()),
    # fully connected, 800 inputs, 500 outputs
    #'fc': tf.Variable(tf.random_normal([n_in_fc, n_hidden])),
    'fc': tf.get_variable('w_fc', shape=[n_in_fc, n_hidden],
           			initializer=tf.contrib.layers.xavier_initializer()),
    # 500 inputs, 10 outputs (class prediction)
    #'out': tf.Variable(tf.random_normal([n_hidden, n_classes]))
    'out': tf.get_variable('w_out', shape=[n_hidden, n_classes],
           			initializer=tf.contrib.layers.xavier_initializer())
}

# biases of LeNet-5 CNN -- tf tensors
biases = {
    'conv1': tf.get_variable('b_conv1', shape=[K1],
           			initializer=tf.zeros_initializer()),
    'conv2': tf.get_variable('b_conv2', shape=[K3],
           			initializer=tf.zeros_initializer()),
    'fc': tf.get_variable('b_fc', shape=[n_hidden],
           			initializer=tf.zeros_initializer()),
    'out': tf.get_variable('b_out', shape=[n_classes],
           			initializer=tf.zeros_initializer()) 
    # 'conv1': tf.Variable(tf.random_normal([K1])),
    # 'conv2': tf.Variable(tf.random_normal([K3])),
    # 'fc': tf.Variable(tf.random_normal([n_hidden])),
    # 'out': tf.Variable(tf.random_normal([n_classes]))
}

def model(x,_W,_b):
	# Reshape input to a 4D tensor 
    x = tf.reshape(x, shape = input_shape)
    # LAYER 1 -- Convolution Layer
    conv1 = tf.nn.relu(tf.nn.conv2d(input = x, 
    								filter =_W['conv1'],
    								strides = [1,S1,S1,1],
    								padding = 'VALID') + _b['conv1'])
    # Layer 2 -- max pool
    conv1 = tf.nn.max_pool(	value = conv1, 
    						ksize = [1, F2, F2, 1], 
    						strides = [1, S2, S2, 1], 
    						padding = 'VALID')

    # LAYER 3 -- Convolution Layer
    conv2 = tf.nn.relu(tf.nn.conv2d(input = conv1, 
    								filter =_W['conv2'],
    								strides = [1,S3,S3,1],
    								padding = 'VALID') + _b['conv2'])
    # Layer 4 -- max pool
    conv2 = tf.nn.max_pool(	value = conv2 , 
    						ksize = [1, F4, F4, 1], 
    						strides = [1, S4, S4, 1], 
    						padding = 'VALID')
    # Fully connected layer
    # Reshape conv2 output to fit fully connected layer
    fc = tf.contrib.layers.flatten(conv2)
    fc = tf.nn.relu(tf.matmul(fc, _W['fc']) + _b['fc'])
    fc = tf.nn.dropout(fc, dropout_rate)

    output = tf.matmul(fc, _W['out']) + _b['out']
    # output = tf.nn.dropout(output, keep_prob = dropout_rate)
    return output

# Construct model
output = model(x,weights,biases)
# Softmax loss
loss = tf.reduce_mean(
	tf.nn.softmax_cross_entropy_with_logits(labels = y, logits = output))
correct_prediction = tf.equal(tf.argmax(output, 1), tf.argmax(y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
# REFERENCE MODEL Parameters -- for training the Reference model: 

# Batch size
minibatch = 512
# Total minibatches
total_minibatches = 100000
# number of minibatches in data
num_minibatches_data = data.train.images.shape[0] // minibatch

# Learning rate
lr = 0.02
# Learning rate decay:  every 2000 minibatches
learning_rate_decay = 0.99
learning_rate_stay_fixed = 1000

# Optimizer: Nesterov accelerated gradient with momentum 0.95
# this is for training the reference net
momentum = 0.9

optimizer = tf.train.MomentumOptimizer(
	learning_rate = learning_rate,
	momentum = momentum_tf,
	use_locking=False,
	name='Momentum',
	use_nesterov=True)

GATE_NONE = 0
GATE_OP = 1
GATE_GRAPH = 2
# GATE_OP:
# For each Op, make sure all gradients are computed before
# they are used.  This prevents race conditions for Ops that generate gradients
# for multiple inputs where the gradients depend on the inputs.
train = optimizer.minimize(
    loss,
    global_step=None,
    var_list=None,
    gate_gradients=GATE_OP,
    aggregation_method=None,
    colocate_gradients_with_ops=False,
    name='train',
    grad_loss=None)


saver = tf.train.Saver()

init = tf.global_variables_initializer()

###############################################################################
######## training data and neural net architecture with weights w #############
###############################################################################
print('----------------------------------------------')
print('LOADING MY PRETRAINED REFERENCE NET for LeNet-5')
print('----------------------------------------------')
################### TO LOAD MODEL #############################################
model_file_name = 'reference_model_lenet_5.ckpt'
model_file_path = './model_lenet_5/' + model_file_name 
model_file_meta = model_file_path + '.meta'
############################## LOAD weights and biases ########################
with tf.Session() as sess:
	saver = tf.train.import_meta_graph(model_file_meta)
	saver.restore(sess, model_file_path)
	w_bar_2 = sess.run(weights)
	bias_bar_2 = sess.run(biases)