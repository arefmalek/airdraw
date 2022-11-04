import cv2
import numpy as np
import glob

from machine.utils.hu_moments_generation import hu_moments_of_file
from machine.utils.label_converters import int_to_label


def load_and_test(model):
    files = glob.glob('../machine/shapes/testing/*')
    for f in files:
        hu_moments = hu_moments_of_file(f) # Genera los momentos de hu de los files de testing
        sample = np.array([hu_moments], dtype=np.float32) # numpy
        testResponse = model.predict(sample)[1] # Predice la clase de cada file

        #Lee la imagen y la imprime con un texto
        image = cv2.imread(f)
        image_with_text = cv2.putText(image, int_to_label(testResponse), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.imshow("result", image_with_text)
        cv2.waitKey(0)
