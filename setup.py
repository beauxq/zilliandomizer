from setuptools import setup  # type: ignore
# https://github.com/pypa/setuptools/issues/2345

if __name__ == "__main__":
    setup(packages=[
        "zilliandomizer",
        "zilliandomizer.options",
        "zilliandomizer.low_resources",
        "zilliandomizer.logic_components",
        "zilliandomizer.map_gen",
        "zilliandomizer.room_gen",
        "zilliandomizer.zri",
        "zilliandomizer.zri.asyncudp",
    ], use_scm_version=True)
