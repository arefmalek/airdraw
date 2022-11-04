from utils.hu_moments_generation import generate_hu_moments_file
from utils.testing_model import load_and_test
from utils.training_model import train_model


def main():
    generate_hu_moments_file()
    model = train_model()
    load_and_test(model)


if __name__ == '__main__':
    main()
