import os

from abc import ABC, abstractmethod
from typing import Optional

import dask.dataframe as dd

from dask_ml.model_selection import train_test_split

from cybulldetection.utils.utils import get_logger


class DatasetReader(ABC):
    required_columns = {"text", "label", "split", "dataset_name"}
    split_names = {"train", "val", "test"}

    def __init__(self, dataset_dir: str, dataset_name: str) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.dataset_dir = dataset_dir
        self.dataset_name = dataset_name

    def read_data(self) -> dd.core.DataFrame:
        self.logger.info(f"Reading {self.__class__.__name__}")
        train_df, val_df, test_df = self._read_data()
        df = self.assign_split_names_to_data_frames_and_merge(train_df, val_df, test_df)
        df["dataset_name"] = self.dataset_name
        if any(required_column not in df.columns.values for required_column in self.required_columns):
            raise ValueError(f"Dataset must contain all required columns: {self.required_columns}")

        unique_split_names = set(df["split"].unique().compute().to_list())
        if unique_split_names != self.split_names:
            raise ValueError(f"Dataset must contain all split names: {self.split_names}")
        final_df: dd.core.DataFrame = df[list(self.required_columns)]
        return final_df

    @abstractmethod
    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        """
        Read and split the dataset into three parts train, validation and test.
        The return value must be a dask dataframes with required columns: self.required_columns
        """
        pass

    def assign_split_names_to_data_frames_and_merge(
        self, train_df: dd.core.DataFrame, val_df: dd.core.DataFrame, test_df: dd.core.DataFrame
    ) -> dd.core.DataFrame:
        train_df["split"] = "train"
        val_df["split"] = "val"
        test_df["split"] = "test" 
        final_df: dd.core.DataFrame = dd.concat([train_df, val_df, test_df]) 
        return final_df

    def split_dataset(
        self, df: dd.core.DataFrame, test_size: float, stratify_column: Optional[str] = None
    ) -> tuple[dd.core.DataFrame, dd.core.DataFrame]:
        if stratify_column is None:
            return train_test_split(df, test_size=test_size, random_state=1234, shuffle=True) # type: ignore
        unique_column_values = df[stratify_column].unique()

        # since dask ml doesn't support stratify, we will create own implementation and return train and val dataframes
        first_dfs = []
        second_dfs = []
        for unique_value in unique_column_values:
            sub_df = df[df[stratify_column] == unique_value]
            sub_df_train, sub_df_val = train_test_split(sub_df, test_size=test_size, random_state=1234, shuffle=True)
            first_dfs.append(sub_df_train)
            second_dfs.append(sub_df_val)

        first_df = dd.concat(first_dfs)  
        second_df = dd.concat(second_dfs) 
        return first_df, second_df 


class GHCDatasetReader(DatasetReader):
    def __init__(self, dataset_dir: str, dataset_name: str, val_split_ratio: float) -> None:
        super().__init__(dataset_dir, dataset_name)
        self.val_split_ratio = val_split_ratio

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        train_tsv_path = os.path.join(self.dataset_dir, "ghc_train.tsv")
        train_df = dd.read_csv(train_tsv_path, sep="\t", header=0)

        test_tsv_path = os.path.join(self.dataset_dir, "ghc_test.tsv")
        test_df = dd.read_csv(test_tsv_path, sep="\t", header=0)

        # combining multiple labels into single binary label
        train_df["label"] = (train_df["hd"] + train_df["cv"] + train_df["vo"] > 0).astype("int")
        test_df["label"] = (test_df["hd"] + test_df["cv"] + test_df["vo"] > 0).astype("int")

        train_df, val_df = self.split_dataset(train_df, self.val_split_ratio, stratify_column="label")

        return train_df, val_df, test_df


class JigsawToxicCommentsDatasetReader(DatasetReader):
    def __init__(self, dataset_dir: str, dataset_name: str, val_split_ratio: float) -> None:
        super().__init__(dataset_dir, dataset_name)
        self.val_split_ratio = val_split_ratio
        self.columns_for_label = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        test_csv_path = os.path.join(self.dataset_dir, "test.csv")
        test_df = dd.read_csv(test_csv_path)

        test_labels_csv_path = os.path.join(self.dataset_dir, "test_labels.csv")
        test_labels_df = dd.read_csv(test_labels_csv_path)

        # merging and removing data points with -1 in the labels
        test_df = test_df.merge(test_labels_df, on=["id"])
        test_df = test_df[test_df["toxic"] != -1]

        test_df = self.get_text_and_label_columns(test_df)

        train_csv_path = os.path.join(self.dataset_dir, "train.csv")
        train_df = dd.read_csv(train_csv_path)

        train_df = self.get_text_and_label_columns(train_df)

        train_df, val_df = self.split_dataset(train_df, self.val_split_ratio, stratify_column="label")

        return train_df, val_df, test_df

    def get_text_and_label_columns(self, df: dd.core.DataFrame) -> dd.core.DataFrame:
        df["label"] = (df[self.columns_for_label].sum(axis=1) > 0).astype("int")
        df = df.rename(columns={"comment_text": "text"})
        return df


class TwitterDatasetReader(DatasetReader):
    def __init__(self, dataset_dir: str, dataset_name: str, val_split_ratio: float, test_split_ratio: float) -> None:
        super().__init__(dataset_dir, dataset_name)
        self.val_split_ratio = val_split_ratio
        self.test_split_ratio = test_split_ratio

    def _read_data(self) -> tuple[dd.core.DataFrame, dd.core.DataFrame, dd.core.DataFrame]:
        df_path = os.path.join(self.dataset_dir, "cyberbullying_tweets.csv")
        df = dd.read_csv(df_path)

        df = df.rename(columns={"tweet_text": "text", "cyberbullying_type": "label"})
        # label zero for type not_cyberbullying and 1 for others
        df["label"] = (df["label"] != "not_cyberbullying").astype("int")

        train_df, test_df = self.split_dataset(df, self.test_split_ratio, stratify_column="label")
        train_df, val_df = self.split_dataset(train_df, self.val_split_ratio, stratify_column="label")

        return train_df, val_df, test_df


# configuration which we set up will use this class to call each dataset reader
class DatasetReaderManager:
    def __init__(self, dataset_readers: dict[str, DatasetReader]) -> None:
        self.dataset_readers = dataset_readers

    def read_data(self) -> dd.core.DataFrame:
        dfs = [dataset_reader.read_data() for dataset_reader in self.dataset_readers.values()]
        df = dd.concat(dfs) 
        return df # type: ignore
