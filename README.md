# cyberbullying data processing Repository

This repository is part of cyberbullying detection in social media project where this repository focuses only on data preprocessing in Google Cloud platfrom with distributed cluster setup. 


In this repository, the objective is as follows 

* Combine three different datasets which are Jigsaw Toxic Comments Dataset, Twitter dataset and GHC dataset into standardized form
* Make all the different labels into a binary clas label with tags as cyberbullying as `label 1` otherwise `label 0`
* Clean the combined dataset using pre-processing strategies 
* Implemented data preprocessing using distributed dask training in Local cluster setup and also GCP cloud setup (via Google cloud compute Engine)
* Incorporated hydra's configuration accordingly to switch between local dask cluster and GCP dask cluster for distributed data preprocessing.

