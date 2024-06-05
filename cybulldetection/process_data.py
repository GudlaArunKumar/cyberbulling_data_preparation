from hydra.utils import instantiate
#from omegaconf import OmegaConf

from cybulldetection.config_schemas.data_processing_config_schema import DataProcessingConfig
from cybulldetection.utils.config_utils import get_config
# from cybulldetection.utils.data_utils import get_raw_data_with_version
# from cybulldetection.utils.gcp_utils import access_secret_version


@get_config(config_path="../configs", config_name="data_processing_config")
def process_data(config: DataProcessingConfig) -> None:
    # github_access_token = access_secret_version(config.infrastructure.project_id, config.github_access_token_secret_id)

    # # calling the function to initiate dowload of data
    # get_raw_data_with_version(
    #     version=config.version,
    #     data_local_save_dir=config.data_local_save_dir,
    #     dvc_remote_repo=config.dvc_remote_repo,
    #     dvc_data_folder=config.dvc_data_folder,
    #     github_user_name=config.github_user_name,
    #     github_access_token=github_access_token
    # )

    dataset_reader_manager = instantiate(
        config.dataset_reader_manager
    )  # this will instantiate ghc_jigsaw_twitter.ymal and then its heirarchy
    dataset_cleaner_manager = instantiate(config.dataset_cleaner_manager)

    df = dataset_reader_manager.read_data().compute()
    # performing cleaning for random 5 data points
    sample_df = df.sample(n=5)

    for _, row in sample_df.iterrows():
        text = row["text"]
        cleaned_text = dataset_cleaner_manager(text)

        print(60 * "=")
        print(f"{text= }")
        print(f"{cleaned_text= }")

    print(df.head())
    print(df["dataset_name"].unique().compute())


if __name__ == "__main__":
    process_data()
