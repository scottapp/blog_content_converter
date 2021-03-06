import argparse, os
import numpy as np

import tensorflow
from tensorflow.keras import backend as K
from tensorflow.keras.optimizers import Adam


class MyCallback(tensorflow.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if logs.get('acc') > 0.998:
            print("\nReached 99% accuracy so cancelling training!")
            self.model.stop_training = True


def create_model(lr):
    model = tensorflow.keras.models.Sequential([
        tensorflow.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
        tensorflow.keras.layers.MaxPooling2D(2, 2),
        tensorflow.keras.layers.Flatten(),
        tensorflow.keras.layers.Dense(128, activation='relu'),
        tensorflow.keras.layers.Dense(10, activation='softmax')
    ])
    model.compile(optimizer=Adam(lr=lr),
                  loss='categorical_crossentropy',
                  metrics=['acc'])
    return model


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--learning-rate', type=float, default=0.001)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--gpu-count', type=int, default=os.environ['SM_NUM_GPUS'])
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--training', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    parser.add_argument('--validation', type=str, default=os.environ['SM_CHANNEL_VALIDATION'])

    args, _ = parser.parse_known_args()

    epochs = args.epochs
    lr = args.learning_rate
    batch_size = args.batch_size
    gpu_count = args.gpu_count
    model_dir = args.model_dir
    training_dir = args.training
    validation_dir = args.validation

    mnist_train_images = np.load(os.path.join(training_dir, 'training.npz'))['image']
    mnist_train_labels = np.load(os.path.join(training_dir, 'training.npz'))['label']
    mnist_test_images  = np.load(os.path.join(validation_dir, 'validation.npz'))['image']
    mnist_test_labels  = np.load(os.path.join(validation_dir, 'validation.npz'))['label']

    K.set_image_data_format('channels_last')
    train_images = mnist_train_images.reshape(mnist_train_images.shape[0], 28, 28, 1)
    test_images = mnist_test_images.reshape(mnist_test_images.shape[0], 28, 28, 1)
    input_shape = (28, 28, 1)

    train_images = train_images.astype('float32')
    test_images = test_images.astype('float32')
    train_images /= 255.0
    test_images /= 255.0

    train_labels = tensorflow.keras.utils.to_categorical(mnist_train_labels, 10)
    test_labels = tensorflow.keras.utils.to_categorical(mnist_test_labels, 10)

    callbacks = MyCallback()
    model = create_model(lr=lr)
    print(model.summary())

    model.fit(train_images,
              train_labels,
              batch_size=batch_size,
              validation_data=(test_images, test_labels),
              epochs=epochs,
              verbose=1,
              callbacks=[callbacks])

    score = model.evaluate(test_images, test_labels, verbose=0)
    print('Validation loss    :', score[0])
    print('Validation accuracy:', score[1])

    # save Keras model for Tensorflow Serving
    sess = K.get_session()
    tensorflow.saved_model.simple_save(
        sess,
        os.path.join(model_dir, 'model/1'),
        inputs={'inputs': model.input},
        outputs={t.name: t for t in model.outputs})
