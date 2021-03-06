# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for Wrapping / Unwrapping dataset variants."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import parameterized

from tensorflow.python.data.kernel_tests import test_base
from tensorflow.python.data.ops import dataset_ops
from tensorflow.python.framework import combinations
from tensorflow.python.framework import ops
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import gen_dataset_ops
from tensorflow.python.platform import test


class WrapDatasetVariantTest(test_base.DatasetTestBase, parameterized.TestCase):

  @combinations.generate(test_base.default_test_combinations())
  def testBasic(self):
    ds = dataset_ops.Dataset.range(100)
    ds_variant = ds._variant_tensor  # pylint: disable=protected-access

    wrapped_variant = gen_dataset_ops.wrap_dataset_variant(ds_variant)
    unwrapped_variant = gen_dataset_ops.unwrap_dataset_variant(wrapped_variant)

    variant_ds = dataset_ops._VariantDataset(unwrapped_variant,
                                             ds.element_spec)
    get_next = self.getNext(variant_ds, requires_initialization=True)
    for i in range(100):
      self.assertEqual(i, self.evaluate(get_next()))

  # TODO(b/123901304)
  @combinations.generate(
      combinations.combine(tf_api_version=[1], mode=["graph"]))
  def testSkipEagerGPU(self):
    ds = dataset_ops.Dataset.range(100)
    ds_variant = ds._variant_tensor  # pylint: disable=protected-access
    wrapped_variant = gen_dataset_ops.wrap_dataset_variant(ds_variant)

    with ops.device("/gpu:0"):
      gpu_wrapped_variant = array_ops.identity(wrapped_variant)

    unwrapped_variant = gen_dataset_ops.unwrap_dataset_variant(
        gpu_wrapped_variant)
    variant_ds = dataset_ops._VariantDataset(unwrapped_variant,
                                             ds.element_spec)
    iterator = dataset_ops.make_initializable_iterator(variant_ds)
    get_next = iterator.get_next()

    with self.cached_session():
      self.evaluate(iterator.initializer)
      for i in range(100):
        self.assertEqual(i, self.evaluate(get_next))


if __name__ == "__main__":
  test.main()
