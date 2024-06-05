import warnings

# ignore rutimewarnings given by _target_ in config schemas by hydra
warnings.filterwarnings(action="ignore", category=RuntimeWarning, module=r".*schema.*")
