# -*- coding: utf-8 -*-
"""Pneumonia detection - DensNet169

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-AhI_I1kzvPpSTj2zCBRby7YFPrH_Gza
"""

from google.colab import drive
drive.mount('/content/drive')
import os
os.chdir('/content/drive/My Drive/IU/Pre-thesis')
!pwd
!ls

BASE_PATH = '/content/drive/My Drive/IU/Pre-thesis'

# Commented out IPython magic to ensure Python compatibility.
import numpy as np # forlinear algebra
import matplotlib.pyplot as plt #for plotting things
# %matplotlib inline
from PIL import Image
print(os.listdir("/content/drive/My Drive/IU/Pre-thesis"))

from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img
from tensorflow.keras.applications import DenseNet169
from tensorflow.keras.layers import Conv2D, MaxPooling2D
from tensorflow.keras.layers import Activation, Dropout, Dense, Flatten
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from imutils import paths
import argparse
import cv2

print(os.listdir("./chest_xray - modified"))

"""Define folder"""

train_folder= './chest_xray - modified/train/'
val_folder = './chest_xray - modified/val/'
test_folder = './chest_xray - modified/test/'

"""Set up training folder"""

os.listdir(train_folder)
train_n = train_folder+'Normal/'
train_p = train_folder+'Pneumonia/'

"""Overview"""

#Normal 
print("Normal training size:" + str(len(os.listdir(train_n))))
rand_norm= np.random.randint(0,len(os.listdir(train_n)))
norm_pic = os.listdir(train_n)[rand_norm]
print('normal picture title: ',norm_pic)

norm_pic_address = train_n + norm_pic

#Pneumonia
print("Pneumonia training size:" + str(len(os.listdir(train_p))))
rand_pneu= np.random.randint(0,len(os.listdir(train_p)))
pneu_pic = os.listdir(train_p)[rand_pneu]
print('pneumonia picture title: ',pneu_pic)

pneu_pic_address = train_p + pneu_pic

# Load the images
norm_load = Image.open(norm_pic_address)
pneu_load = Image.open(pneu_pic_address)

#Let's plot these images
figure = plt.figure(figsize= (10,6))
a1 = figure.add_subplot(1,2,1)
img_plot = plt.imshow(norm_load,cmap = "gray")
a1.set_title('Normal')

a2 = figure.add_subplot(1,2,2)
img_plot = plt.imshow(pneu_load, cmap = "gray")
a2.set_title('Pneumonia')

"""# Pre-processing data"""

img_size = 300
number_classes = 2
epochs = 30
batch_size = 16

# initialize the training data augmentation object
train_data_gen = ImageDataGenerator(
    rescale            = 1.0/255.0,
    rotation_range     = 40       , 
    width_shift_range  = 0.2      ,
    height_shift_range = 0.2      ,
    shear_range        = 0.2      ,
    zoom_range         = 0.2      ,
    horizontal_flip    = True     ,
    vertical_flip      = False    )
# initialize the validation data augmentation object
val_data_gen = ImageDataGenerator(rescale=1./255)
# initialize the testing data augmentation object
test_data_gen = ImageDataGenerator(rescale=1./255)

# initialize the training generator
train_data = train_data_gen.flow_from_directory(
    train_folder, 
    batch_size = batch_size,
    target_size = (img_size,img_size),
    class_mode = 'binary')
# initialize the validation generator
val_data = val_data_gen.flow_from_directory(
    val_folder,
    shuffle = False,
    batch_size = batch_size,
    target_size = (img_size,img_size),
    class_mode = 'binary')

# initialize the testing generator
test_data = test_data_gen.flow_from_directory(
    test_folder,
    shuffle = False,
    batch_size = batch_size,
    target_size = (img_size,img_size),
    class_mode = 'binary')

"""# Building model"""

from tensorflow.keras.applications import DenseNet169

base_model = DenseNet169(input_shape = (300,300,3), include_top = False, weights='imagenet')

model = Sequential()
model.add(base_model)
model.add(Conv2D(512,
                 activation='relu',
                 kernel_size=3,
                 input_shape = (300,300,3)))
model.add(MaxPooling2D(pool_size=(2,2)))
#FC layers
model.add(Flatten())
model.add(Dense(512, activation = 'relu'))
model.add(Dropout(0.7))
model.add(Dense(128, activation = 'relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation = 'relu'))
model.add(Dropout(0.3))
model.add(Dense(1, activation = 'sigmoid'))
model.summary()

"""# Training model"""

import tensorflow.keras.callbacks
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping

# Compile model
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['acc'])

# Callbacks
checkpoint = tensorflow.keras.callbacks.ModelCheckpoint("Pneumonia.h5", 
                                             monitor="val_acc",
                                             save_best_only=True, 
                                             save_weights_only=True)

lr_reduce = ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=2, verbose=2, mode='max')
early_stop = EarlyStopping(monitor='val_loss', min_delta=0.1, patience=1, mode='min')

train_history = model.fit(train_data,
                                    steps_per_epoch = train_data.samples // batch_size,
                                    epochs = epochs,
                                    validation_data = val_data,
                                    validation_steps = val_data.samples // batch_size,
                                    callbacks = [checkpoint, lr_reduce])

from tensorflow.python.keras.models import load_model
model.save('Pneumonia.h5')
model = load_model("/content/drive/My Drive/IU/Pre-thesis/Pneumonia.h5")

plt.plot(train_history.history['acc'], 'r', label='Training data')
plt.plot(train_history.history['val_acc'], 'g', label='Validation data')
plt.title('Model Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend()
plt.show()

# summarize history for loss
plt.plot(train_history.history['loss'], label='Training data')
plt.plot(train_history.history['val_loss'], label='Validation data')
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend()
plt.show()

"""## Confusion matrix"""

from tensorflow.python.keras.models import load_model
model = load_model("/content/drive/My Drive/IU/Pre-thesis/Pneumonia.h5")

from sklearn.metrics import classification_report
from mlxtend.plotting import plot_confusion_matrix
from sklearn.metrics import confusion_matrix

"""## Val set"""

val_pred = val_data_gen.flow_from_directory(
    val_folder,
    shuffle = False,
    batch_size = 1,
    target_size = (img_size,img_size),
    class_mode = 'binary')

val_prediction = model.predict_generator(val_pred, verbose=1,steps=len(val_pred))

val_prediction.shape

label=val_data.classes

val_pred2=val_prediction>0.5
print(classification_report(label,val_pred2))

# Get the confusion matrix
cm=confusion_matrix(label, val_pred2)
plt.figure()
plot_confusion_matrix(cm,figsize=(5,5), hide_ticks=True,cmap=plt.cm.Blues)
plt.xticks(range(2), ['Normal', 'Pneumonia'], fontsize=10)
plt.yticks(range(2), ['Normal', 'Pneumonia'], fontsize=10)
plt.show()

"""## Test set"""

test_pred = test_data_gen.flow_from_directory(
    test_folder,
    shuffle = False,
    batch_size = 1,
    target_size = (img_size,img_size),
    class_mode = 'binary')

test_prediction = model.predict_generator(test_pred, verbose=1,steps=len(test_pred))

test_prediction.shape

import itertools
test_label=test_data.classes
test_pred2=test_prediction>0.5
print(classification_report(test_label,test_pred2))

# Get the confusion matrix
cm  = confusion_matrix(test_label, test_pred2)
plt.figure()
plot_confusion_matrix(cm,figsize=(5,5), hide_ticks=True,cmap=plt.cm.Blues)
plt.xticks(range(2), ['Normal', 'Pneumonia'], fontsize=10)
plt.yticks(range(2), ['Normal', 'Pneumonia'], fontsize=10)
plt.show()

