import unittest

import pandas as pd
import numpy as np
from pymatgen import Structure

from matbench.task import MatbenchTask
from matbench.metadata import metadata


import warnings
import traceback
import sys



class TestMatbenchTask(unittest.TestCase):

    def setUp(self) -> None:
        self.test_datasets = ["matbench_dielectric", "matbench_steels", "matbench_glass"]
        self.shuffle_seed = 1001

        # def warn_with_traceback(message, category, filename, lineno, file=None,
        #                         line=None):
        #     log = file if hasattr(file, 'write') else sys.stderr
        #     traceback.print_stack(file=log)
        #     log.write(
        #         warnings.formatwarning(message, category, filename, lineno,
        #                                line))
        #
        # warnings.showwarning = warn_with_traceback

    def test_instantiation(self):
        for ds in self.test_datasets:
            mbt = MatbenchTask(ds)

    def test_get_train_and_val_data(self):
        # Assuming 5-fold nested cross validation
        for ds in self.test_datasets:
            mbt = MatbenchTask(ds)
            # shuffle seed must be set because it shuffles the (same) training data in a deterministic manner
            inputs, outputs = mbt.get_train_and_val_data(fold_number=0, as_type="tuple", shuffle_seed=self.shuffle_seed)


            self.assertListEqual(inputs.index.tolist(), outputs.index.tolist())
            self.assertEqual(inputs.shape[0], int(np.floor(mbt.df.shape[0] * 4/5)))
            self.assertEqual(outputs.shape[0], int(np.floor(mbt.df.shape[0] * 4/5)))

            input_type = Structure if mbt.metadata.input_type == "structure" else str
            output_type = float if mbt.metadata.task_type == "regression" else bool
            self.assertTrue(all([isinstance(d, input_type) for d in inputs]))
            self.assertTrue(all([isinstance(d, output_type) for d in outputs]))


            if ds == "matbench_dielectric":
                sio2 = inputs.iloc[101].composition.reduced_formula
                self.assertEqual(sio2, "SiO2")
                self.assertEqual(sio2, inputs.loc[2658].composition.reduced_formula) # loc index corresponds to the iloc in the original df
                self.assertEqual(sio2, mbt.df["structure"].iloc[2658].composition.reduced_formula)                # make sure the index matches the original df
                n = 1.5191342929445046
                self.assertAlmostEqual(outputs.iloc[101], n, places=10)
                self.assertAlmostEqual(outputs.loc[2658], n, places=10)
                self.assertAlmostEqual(mbt.df["n"].iloc[2658], n, places=10)
            elif ds == "matbench_steels":
                alloy = "Fe0.755C0.00552Mn0.00543Si0.0236Cr0.128Ni0.0188Mo0.0173V0.00380N0.00197Nb0.00244Co0.0375Al0.000615"
                self.assertEqual(alloy, inputs.iloc[101])
                self.assertEqual(alloy, inputs.loc[202]) # loc index corresponds to the iloc in the original df
                self.assertEqual(alloy, mbt.df["composition"].iloc[202]) # make sure the index matches the original df
                yield_strength = 1074.9
                self.assertAlmostEqual(outputs.iloc[101], yield_strength, places=5)
                self.assertAlmostEqual(outputs.loc[202], yield_strength, places=5)
                self.assertAlmostEqual(mbt.df["yield strength"].iloc[202], yield_strength, places=5)
            elif ds == "matbench_glass":
                alloy = "Ti19Al31"
                self.assertEqual(alloy, inputs.iloc[101])
                self.assertEqual(alloy, inputs.loc[4226]) # loc index corresponds to the iloc in the original df
                self.assertEqual(alloy, mbt.df["composition"].iloc[4226]) # make sure the index matches the original df
                gfa = True
                self.assertEqual(outputs.iloc[101], gfa)
                self.assertEqual(outputs.loc[4226], gfa)
                self.assertEqual(mbt.df["gfa"].iloc[4226], gfa)

    def test_get_test_data(self):
        for ds in self.test_datasets:
            mbt = MatbenchTask(ds)
            folds = []
            for fold in mbt.folds:
                inputs, outputs = mbt.get_test_data(fold_number=fold, as_type="tuple")

                self.assertListEqual(inputs.index.tolist(), outputs.index.tolist())

                upper_bound = int(np.ceil(mbt.df.shape[0]/5))
                allowed_fold_sizes = (upper_bound - 1, upper_bound)
                self.assertTrue(inputs.shape[0] in allowed_fold_sizes)
                self.assertTrue(outputs.shape[0] in allowed_fold_sizes)
                input_type = Structure if mbt.metadata.input_type == "structure" else str
                output_type = float if mbt.metadata.task_type == "regression" else bool
                self.assertTrue(all([isinstance(d, input_type) for d in inputs]))
                self.assertTrue(all([isinstance(d, output_type) for d in outputs]))
                folds.append((inputs, outputs))

            # check if all entries from original df are in exactly one test fold exactly once
            original_input_df = mbt.df[mbt.metadata.input_type]
            inputs_from_folds = pd.concat([f[0] for f in folds])
            self.assertEqual(inputs_from_folds.shape[0], original_input_df.shape[0])
            self.assertTrue(original_input_df.apply(lambda i: i in inputs_from_folds.tolist()).all())


            # Test individual samples from an individual test set
            inputs, outputs = folds[0]
            if ds == "matbench_dielectric":
                ki = inputs.iloc[12].composition.reduced_formula
                self.assertEqual(ki, "KI")
                self.assertEqual(ki, inputs.loc[75].composition.reduced_formula) # loc index corresponds to the iloc in the original df
                self.assertEqual(ki, mbt.df["structure"].iloc[75].composition.reduced_formula)                # make sure the index matches the original df
                n = 1.7655027612552967
                self.assertAlmostEqual(outputs.iloc[12], n, places=10)
                self.assertAlmostEqual(outputs.loc[75], n, places=10)
                self.assertAlmostEqual(mbt.df["n"].iloc[75], n, places=10)
            elif ds == "matbench_steels":
                alloy = "Fe0.682C0.00877Mn0.000202Si0.00967Cr0.134Ni0.00907Mo0.00861V0.00501Nb0.0000597Co0.142Al0.000616"
                self.assertEqual(alloy, inputs.iloc[12])
                self.assertEqual(alloy, inputs.loc[67]) # loc index corresponds to the iloc in the original df
                self.assertEqual(alloy, mbt.df["composition"].iloc[67]) # make sure the index matches the original df
                yield_strength = 1241.0
                self.assertAlmostEqual(outputs.iloc[12], yield_strength, places=5)
                self.assertAlmostEqual(outputs.loc[67], yield_strength, places=5)
                self.assertAlmostEqual(mbt.df["yield strength"].iloc[67], yield_strength, places=5)
            elif ds == "matbench_glass":
                alloy = "Al13VCu6"
                self.assertEqual(alloy, inputs.iloc[12])
                self.assertEqual(alloy, inputs.loc[55]) # loc index corresponds to the iloc in the original df
                self.assertEqual(alloy, mbt.df["composition"].iloc[55]) # make sure the index matches the original df
                gfa = True
                self.assertEqual(outputs.iloc[12], gfa)
                self.assertEqual(outputs.loc[55], gfa)
                self.assertEqual(mbt.df["gfa"].iloc[55], gfa)





