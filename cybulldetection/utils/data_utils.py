from shutil import rmtree

from cybulldetection.utils.utils import run_shell_command


def get_cmd_to_get_raw_data(
    version: str,
    data_local_save_dir: str,
    dvc_remote_repo: str,
    dvc_data_folder: str,
    github_user_name: str,
    github_access_token: str,
) -> str:
    """
    Get shell command to download the raw data from dvc storage

    Parameters
    ----------
    version: str
        data version
    data_local_save_dir: str
        lcoation to save the downloaded data locally
    dvc_remote_repo: str
        dvc/git repository that holds information about the data
    dvc_data_folder: str
        location of the folder where the remote data is stored
    github_user_name: str
        github user name
    github_access_token: str
        github access token

    Returns
    -------
    str
        shell command to download the raw data from dvc store
    """

    without_https = dvc_remote_repo.replace("https://", "")
    dvc_remote_repo = f"https://{github_user_name}:{github_access_token}@{without_https}"
    command = f"dvc get {dvc_remote_repo} {dvc_data_folder} --rev {version} -o {data_local_save_dir}"
    return command


def get_raw_data_with_version(
    version: str,
    data_local_save_dir: str,
    dvc_remote_repo: str,
    dvc_data_folder: str,
    github_user_name: str,
    github_access_token: str,
) -> None:
    # remove the local directory if it is already present with previous version
    rmtree(data_local_save_dir, ignore_errors=True)

    # command to download the required raw data folder to local working directory
    command = get_cmd_to_get_raw_data(
        version, data_local_save_dir, dvc_remote_repo, dvc_data_folder, github_user_name, github_access_token
    )
    run_shell_command(command)
