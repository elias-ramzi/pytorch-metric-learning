import unittest
import torch
from pytorch_metric_learning.reducers import ClassWeightedReducer

class TestClassWeightedReducer(unittest.TestCase):
    def test_class_weighted_reducer(self):
        class_weights = torch.tensor([1, 0.9, 1, 0.1, 0, 0, 0, 0, 0, 0])
        reducer = ClassWeightedReducer(class_weights)
        batch_size = 100
        num_classes = 10
        embedding_size = 64
        embeddings = torch.randn(batch_size, embedding_size)
        labels = torch.randint(0,num_classes,(batch_size,))
        pair_indices = (torch.randint(0,batch_size,(batch_size,)), torch.randint(0,batch_size,(batch_size,)))
        triplet_indices = pair_indices + (torch.randint(0,batch_size,(batch_size,)),)
        losses = torch.randn(batch_size)

        for indices, reduction_type in [(torch.arange(batch_size), "element"),
                                        (pair_indices, "pos_pair"),
                                        (pair_indices, "neg_pair"),
                                        (triplet_indices, "triplet")]:
            loss_dict = {"loss": {"losses": losses, "indices": indices, "reduction_type": reduction_type}}
            output = reducer(loss_dict, embeddings, labels)
            correct_output = 0
            for i in range(len(losses)):
                if reduction_type == "element":
                    batch_idx = indices[i]
                else:
                    batch_idx = indices[0][i]
                class_label = labels[batch_idx]
                correct_output += losses[i]*class_weights[class_label]
            correct_output /= len(losses)
            self.assertTrue(torch.isclose(output,correct_output))