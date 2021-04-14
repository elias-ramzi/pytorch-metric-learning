import itertools

from torch.utils.data.sampler import BatchSampler

from ..utils import common_functions as c_f


# Inspired by
# https://github.com/kunhe/Deep-Metric-Learning-Baselines/blob/master/datasets.py
class HierarchicalSampler(BatchSampler):
    def __init__(
        self,
        labels,
        batch_size,
        samples_per_class,
        batches_per_super_pair,
        nb_categories=2,
        inner_label=0,
        outer_label=1,
    ):
        """
        labels: 2D array, where rows correspond to elements, and columns correspond to the hierarchical labels
        batch_size: because this is a BatchSampler the batch size must be specified
        samples_per_class: number of instances to sample for a specific class. set to 0 if all element in a class
        batches_per_super_pairs: number of batches to create for a pair of categories (or super labels)
        inner_label: columns index corresponding to classes
        outer_label: columns index corresponding to the level of hierarchy for the pairs
        """
        self.batch_size = batch_size
        self.batches_per_super_pair = batches_per_super_pair
        self.samples_per_class = samples_per_class
        self.nb_categories = nb_categories

        # checks
        assert self.batch_size % nb_categories == 0, f"batch_size should be a multiple of {nb_categories}"
        self.sub_batch_len = self.batch_size // nb_categories
        if self.samples_per_class > 0:
            assert self.sub_batch_len % self.samples_per_class == 0, "batch_size not a multiple of samples_per_class"
        else:
            self.samples_per_class = len(labels)

        all_super_labels = set(labels[:, outer_label])
        self.super_image_lists = {slb: {} for slb in all_super_labels}
        for idx, instance in enumerate(labels):
            slb, lb = instance[outer_label], instance[inner_label]
            try:
                self.super_image_lists[slb][lb].append(idx)
            except KeyError:
                self.super_image_lists[slb][lb] = [idx]

        self.super_pairs = list(itertools.combinations(all_super_labels, nb_categories))
        self.reshuffle()

    def __iter__(self,):
        self.reshuffle()
        for batch in self.batches:
            yield batch

    def __len__(self,):
        return len(self.batches)

    def reshuffle(self):
        batches = []
        for combinations in self.super_pairs:

            for b in range(self.batches_per_super_pair):

                batch = []
                for slb in combinations:

                    sub_batch = []
                    all_classes = list(self.super_image_lists[slb].keys())
                    c_f.NUMPY_RANDOM.shuffle(all_classes)
                    for cl in all_classes:
                        instances = self.super_image_lists[slb][cl]
                        if len(sub_batch) + min(len(instances), self.samples_per_class) > self.sub_batch_len:
                            continue

                        sub_batch.extend(
                            c_f.NUMPY_RANDOM.choice(instances, size=min(len(instances), self.samples_per_class), replace=False)
                        )

                    batch.extend(sub_batch)

                c_f.NUMPY_RANDOM.shuffle(batch)
                batches.append(batch)

        c_f.NUMPY_RANDOM.shuffle(batches)
        self.batches = batches