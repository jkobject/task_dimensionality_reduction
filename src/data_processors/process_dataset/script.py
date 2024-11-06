import sys

import anndata as ad
import openproblems as op
import numpy as np
from sklearn.metrics import pairwise_distances

## VIASH START
par = {
    "input": "resources_test/common/cxg_mouse_pancreas_atlas/dataset.h5ad",
    "output_dataset": "dataset.h5ad",
    "output_solution": "solution.h5ad",
}
meta = {
    "resources_dir": "target/executable/data_processors/process_dataset",
    "config": "target/executable/data_processors/process_dataset/.config.vsh.yaml",
}
## VIASH END

# import helper functions
sys.path.append(meta["resources_dir"])
from subset_h5ad_by_format import subset_h5ad_by_format

print("====== Dataset processor ======", flush=True)

print("\n>>> Reading processor config...", flush=True)
config = op.project.read_viash_config(meta["config"])

print("\n>>> Reading raw dataset...", flush=True)
adata = ad.read_h5ad(par["input"])
print(adata, flush=True)

print("\n>>> Selecting waypoint cells...", flush=True)
if adata.n_obs < 10000:
    waypoint_cells = adata.obs_names
else:
    np.random.seed(0)  # Try to get the same cells each time
    waypoint_cells = np.random.choice(adata.obs_names, 10000, replace=False)
adata.obs["is_waypoint"] = adata.obs_names.isin(waypoint_cells)

print("\n>>> Calculating waypoint distances...", flush=True)
adata.obsm["waypoint_distances"] = pairwise_distances(
    adata.layers["normalized"],
    adata.layers["normalized"][adata.obs["is_waypoint"].values, :],
    metric="euclidean",
    n_jobs = -2
)

print("\n>>> Calculating label centroids...", flush=True)
normalized_mat = adata.layers["normalized"].todense()
labels = np.unique(adata.obs["cell_type"])
centroids = np.zeros((len(labels), normalized_mat.shape[1]))
for i, label in enumerate(labels):
    is_label = adata.obs["cell_type"] == label
    centroids[i, :] = np.mean(normalized_mat[is_label, :], axis=0)

adata.uns["label_centroids"] = centroids

print("\n>>> Calculating centroid distances...", flush=True)
adata.obsm["centroid_distances"] = pairwise_distances(
    adata.layers["normalized"],
    centroids,
    metric="euclidean",
    n_jobs = -2
)

print("\n>>> Creating input data...", flush=True)
output_dataset = subset_h5ad_by_format(adata, config, "output_dataset")
print(output_dataset, flush=True)

print("\n>>> Creating solution data...", flush=True)
output_solution = subset_h5ad_by_format(adata, config, "output_solution")
print(output_solution, flush=True)

print("\n>>> Writing data files...", flush=True)
output_dataset.write_h5ad(par["output_dataset"])
print(f"Output dataset file: '{par['output_dataset']}'", flush=True)
output_solution.write_h5ad(par["output_solution"])
print(f"Output solution file: '{par['output_solution']}'", flush=True)

print("\n>>> Done!", flush=True)
