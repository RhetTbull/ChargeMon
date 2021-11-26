from setuptools import setup

APP = ["chargemon.py"]
DATA_FILES = ["chargemon_plugged.png", "chargemon_unplugged.png"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "LSUIElement": True,
    },
    "packages": ["rumps", "psutil"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
