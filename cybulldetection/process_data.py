import os

from hydra.utils import instantiate
from omegaconf import OmegaConf

from pathlib import Path

from dask.distributed import Client
import dask.dataframe as dd

from cybulldetection.config_schemas.data_processing_config_schema import DataProcessingConfig
from cybulldetection.config_schemas.data_processing.dataset_cleaners_schema import DatasetCleanerManagerConfig
from cybulldetection.utils.config_utils import get_pickle_config, custom_instantiate
from cybulldetection.utils.utils import get_logger
from cybulldetection.utils.io_utils import write_yaml_file
from cybulldetection.utils.data_utils import filter_based_on_minimum_number_of_words
# from cybulldetection.utils.gcp_utils import access_secret_version

def process_raw_data(df_partition: dd.core.DataFrame, dataset_cleaner_manager: DatasetCleanerManagerConfig) -> dd.core.Series:

    # this will call each pre-processing class defined in dataset cleaners
    return df_partition["text"].apply(dataset_cleaner_manager)


@get_pickle_config(config_path="cybulldetection/configs/automatically_generated", config_name="data_processing_config")
def process_data(config: DataProcessingConfig) -> None:

    logger = get_logger(Path(__file__).name)
    logger.info("Processing the raw data using dask local cluster")

    processed_data_save_dir = config.processed_data_save_dir

    cluster = custom_instantiate(config.dask_cluster) # this will instantiate LocalCluster with all defined params 
    client = Client(cluster)

    # now dask cluster is instantiated and running with 12 cores (worker nodes in 1 cpu)
    try:
        dataset_reader_manager = instantiate(
            config.dataset_reader_manager
        )  # this will instantiate ghc_jigsaw_twitter.ymal and then its heirarchy
        dataset_cleaner_manager = instantiate(config.dataset_cleaner_manager)

        df = dataset_reader_manager.read_data(config.dask_cluster.n_workers)

        logger.info("cleaning the data....")
        df = df.assign(cleaned_text=df.map_partitions(process_raw_data, dataset_cleaner_manager=dataset_cleaner_manager, 
                       meta=("text", "object"))) 
        
        df = df.compute()

        train_parquet_path = os.path.join(processed_data_save_dir, "train.parquet")
        val_parquet_path = os.path.join(processed_data_save_dir, "val.parquet")
        test_parquet_path = os.path.join(processed_data_save_dir, "test.parquet")

        train_df = df[df["split"] == "train"]
        val_df = df[df["split"] == "val"]
        test_df = df[df["split"] == "test"]

        train_df = filter_based_on_minimum_number_of_words(train_df, min_no_of_words=config.min_no_of_words)
        val_df = filter_based_on_minimum_number_of_words(val_df, min_no_of_words=config.min_no_of_words)
        test_df = filter_based_on_minimum_number_of_words(test_df, min_no_of_words=config.min_no_of_words)

        train_df.to_parquet(train_parquet_path)
        val_df.to_parquet(val_parquet_path)
        test_df.to_parquet(test_parquet_path)

        docker_info = {"docker_image": config.docker_image_name, "docker_tag": config.docker_image_tag}
        docker_info_save_path = os.path.join(processed_data_save_dir, "docker_info.yaml")

        write_yaml_file(docker_info_save_path, docker_info) # writing it to gcs bucket

        logger.info("Data Processing finished..")

    finally:
        logger.info("closing the cluster ...")
        client.close()
        cluster.close()


if __name__ == "__main__":
    process_data()
