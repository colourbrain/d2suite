from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import geodesic_wasserstein_classification as gwc
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.contrib.learn.python.learn.datasets.mnist import DataSet

from sklearn.linear_model import LogisticRegression
from tqdm import tqdm

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_boolean('is_train', False,
                            """Whether to train """)

tf.app.flags.DEFINE_float('learning_rate', 1.,
                          """ the learning rate in sgd """)

tf.app.flags.DEFINE_integer('image_size', 20,
                            """ """)

tf.app.flags.DEFINE_integer('batch_size', 64, """ """)

tf.app.flags.DEFINE_integer('total_steps', 10000, """ """)

tf.app.flags.DEFINE_string('log_dir', '/tmp/mnist_d2_logs', """ """)

tf.app.flags.DEFINE_integer('mu_nbins', 1, 
                            """ number of vectors in d2 representation of mu""")

def get_two_classes(dataset, a, b):
    select = np.where(dataset.labels[:,a] + dataset.labels[:,b] > 0)
    train_labels = np.squeeze(dataset.labels[select,a])
    train_images = dataset.images[select]
    return train_images, train_labels

def get_M():
    M = np.zeros(shape = [ FLAGS.image_size *  FLAGS.image_size,  FLAGS.image_size *  FLAGS.image_size, 2], dtype = np.float32)
    for i in range(FLAGS.image_size*FLAGS.image_size):
        for j in range(FLAGS.image_size*FLAGS.image_size):
            xi = np.floor(i /FLAGS.image_size)
            yi = i % FLAGS.image_size
            xj = np.floor(j /FLAGS.image_size)
            yj = j % FLAGS.image_size
            M[i,j,0] = xi - xj
            M[i,j,1] = yi - yj
    return M

def get_V(num_samples):
    V = np.zeros(shape = [num_samples, FLAGS.image_size * FLAGS.image_size, 2], dtype = np.float32)
    for i in range(FLAGS.image_size):
        for j in range(FLAGS.image_size):
            for k in range(num_samples):
                V[k, i*FLAGS.image_size + j, 0] = i
                V[k, i*FLAGS.image_size + j, 1] = j
    return V

def get_crop_mask():
    mask = np.full(784, False)
    padding = FLAGS.image_size / 2
    for i in range(784):
        x = np.floor(i / 28)
        y = i % 28
        mask[i] = np.abs(x - 13.5) < padding and np.abs(y - 13.5) < padding
    return mask

if __name__ == "__main__":
    mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)
    mask = get_crop_mask()
    train_images, train_labels = get_two_classes(mnist.train, 4, 9)
    train_images = train_images[:FLAGS.batch_size]
    train_images = train_images[:, mask]
    train_labels = train_labels[:FLAGS.batch_size]
    test_images, test_labels = get_two_classes(mnist.test, 4, 9)
    test_images = test_images[:, mask]

    lr = LogisticRegression()
    lr.fit(train_images, train_labels)
    print('lr test accuracy: %f' % lr.score(test_images, test_labels))


    train_dataset = DataSet(train_images, train_labels, reshape=False)
    test_dataset = DataSet(test_images, test_labels, reshape=False)

    batch_size = FLAGS.batch_size
    

    w = tf.placeholder(shape=[batch_size, FLAGS.image_size * FLAGS.image_size], dtype = tf.float32)
    nw = w / tf.reduce_sum(w, 1, keep_dims=True)
    label = tf.placeholder(shape=[batch_size], dtype = tf.float32)
    V = tf.constant(get_V(batch_size))
    global_step = tf.train.get_or_create_global_step()    

    with tf.variable_scope("gwc", reuse=tf.AUTO_REUSE):
        logit = gwc.gwc_d2_model(nw, V, mu_nbins = FLAGS.mu_nbins)
        loss, dLW = gwc.get_losses_gradients(logit, label, use_d2 = True)
        one_step = gwc.update_one_step(dLW, learning_rate = FLAGS.learning_rate,
                                       step = global_step, use_d2 = True)
        tf.summary.scalar('loss', loss)
        accuracy = gwc.get_accuracy(logit, label)

    loss = tf.Print(loss, [loss], message = "loss: ")
    init = tf.global_variables_initializer()


    saver = tf.train.Saver(tf.global_variables())

    merged = tf.summary.merge_all()
    writer = tf.summary.FileWriter(FLAGS.log_dir)


    config = tf.ConfigProto()
    config.intra_op_parallelism_threads = 1
    config.inter_op_parallelism_threads = 4
    config.gpu_options.allow_growth=True
    if FLAGS.is_train:
        ckpt = tf.train.get_checkpoint_state(FLAGS.log_dir)
        with tf.Session(config=config) as sess:
            sess.run(init)
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)
            for i in range(FLAGS.total_steps):
                batch = train_dataset.next_batch(batch_size, shuffle=True)
                if (i+1) % 10 == 0:
                    summary, loss_v = sess.run([merged, loss],
                                           feed_dict = {w: batch[0], label: batch[1]})
                    writer.add_summary(summary, global_step.eval())
                
                sess.run(one_step, feed_dict = {w: batch[0], label: batch[1]})
                if (i+1) % 50 == 0:
                    saver.save(sess, FLAGS.log_dir + '/param',
                               global_step = global_step.eval(), write_meta_graph=False)
    else:
        ckpt = tf.train.get_checkpoint_state(FLAGS.log_dir)
        with tf.Session(config=config) as sess:
            saver.restore(sess, ckpt.model_checkpoint_path)
            train_batch = train_dataset.next_batch(batch_size, shuffle=False)
            train_acc = sess.run(accuracy, feed_dict = {w: train_batch[0], label: train_batch[1]})
            print('train accuracy: %f' % train_acc)
            acc_v = 0
            count = 0
            for i in tqdm(range(int(test_dataset.num_examples / batch_size))):
                test_batch = test_dataset.next_batch(batch_size, shuffle=False)
                acc_v += sess.run(accuracy, feed_dict = {w: test_batch[0], label: test_batch[1]})
                count += 1
                # print('batch #d: %f' % i, acc_v / count)
            acc_v /= count;
            print('test accuracy: %f' % acc_v)
