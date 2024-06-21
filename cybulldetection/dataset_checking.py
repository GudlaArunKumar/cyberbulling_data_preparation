
import pandas as pd 

df = pd.read_parquet("gs://cybull_detection/data/processed/rebalanced_val_test_splits/test.parquet")

# to check whether filter is applied
print(df[df["cleaned_text"].str.split().apply(len) < 2])
print(df.shape)



