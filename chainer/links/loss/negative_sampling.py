import numpy

from chainer.backends import cuda
from chainer.functions.loss import negative_sampling
from chainer import link
from chainer.utils import argument
from chainer.utils import walker_alias
from chainer import variable


class NegativeSampling(link.Link):

    """Negative sampling loss layer.

    This link wraps the :func:`~chainer.functions.negative_sampling` function.
    It holds the weight matrix as a parameter. It also builds a sampler
    internally given a list of word counts.

    Args:
        in_size (int): Dimension of input vectors.
        counts (int list): Number of each identifiers.
        sample_size (int): Number of negative samples.
        power (float): Power factor :math:`\\alpha`.

    .. seealso:: :func:`~chainer.functions.negative_sampling` for more detail.

    Attributes:
        W (~chainer.Variable): Weight parameter matrix.

    """

    def __init__(self, in_size, counts, sample_size, power=0.75):
        super(NegativeSampling, self).__init__()
        vocab_size = len(counts)
        self.sample_size = sample_size
        power = numpy.float32(power)
        p = numpy.array(counts, power.dtype)
        numpy.power(p, power, p)
        self.sampler = walker_alias.WalkerAlias(p)

        with self.init_scope():
            self.W = variable.Parameter(0, (vocab_size, in_size))

    def to_cpu(self):
        super(NegativeSampling, self).to_cpu()
        self.sampler.to_cpu()
        return self

    def to_gpu(self, device=None):
        with cuda._get_device(device):
            super(NegativeSampling, self).to_gpu()
            self.sampler.to_gpu()
        return self

    def forward(self, x, t, reduce='sum', **kwargs):
        """forward(x, t, reduce='sum', *, return_samples=False)

        Computes the loss value for given input and ground truth labels.

        Args:
            x (~chainer.Variable): Input of the weight matrix multiplication.
            t (~chainer.Variable): Batch of ground truth labels.
            reduce (str): Reduction option. Its value must be either
                ``'sum'`` or ``'no'``. Otherwise, :class:`ValueError` is
                raised.
            return_samples (bool):
                If ``True``, the sample array taken by the sampler is also
                returned.

        Returns:
            ~chainer.Variable or tuple:
                If ``return_samples`` is ``False`` (default), loss value is
                returned.

                Otherwise, a tuple of the loss value and the sample array taken
                by the sampler is returned.

        """
        return_samples = False
        if kwargs:
            return_samples, = argument.parse_kwargs(
                kwargs, ('return_samples', return_samples))

        ret = negative_sampling.negative_sampling(
            x, t, self.W, self.sampler.sample, self.sample_size,
            reduce=reduce, return_samples=return_samples)
        return ret
