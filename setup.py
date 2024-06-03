"""" Setup script to generate an executable. """
from cx_Freeze import Executable, setup

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "includes": ["selenium", "time", "os", "datetime"],
}

setup(
    name="RECUP_CFE",
    version="1.0",
    description="Récupération de CFE",
    options={"build_exe": build_exe_options},
    executables=[Executable("RECUP_CFE.py")],
)
