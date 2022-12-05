import cv2
import csv

import numpy as np

from machine.utils.label_converters import label_to_int

trainData = []
trainLabels = []


# Agarro las cosas en los archivos las guardo en variables y las mando a train data y labels
def load_training_set():
    global trainData
    global trainLabels
    with open('machine/generated-files/shapes-hu-moments.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            class_label = row.pop()  # saca el ultimo elemento de la lista
            floats = []
            for n in row:
                floats.append(float(n))  # tiene los momentos de Hu transformados a float.
            trainData.append(np.array(floats, dtype=np.float32))  # momentos de Hu
            trainLabels.append(np.array([label_to_int(class_label)], dtype=np.int32))  # Resultados
            # Valores y resultados se necesitan por separados
    trainData = np.array(trainData, dtype=np.float32)
    trainLabels = np.array(trainLabels, dtype=np.int32)


# transforma los arrays a arrays de forma numpy


# llama la funcion de arriba, se manda a entrenar y devuelve el modelo entrenado
def train_model():
    load_training_set()

    tree = cv2.ml.DTrees_create()
    tree.setCVFolds(1)
    tree.setMaxDepth(10)
    tree.train(trainData, cv2.ml.ROW_SAMPLE, trainLabels)
    tree.save("model.yml")
    return tree
