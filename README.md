# build-mod

Packages a single Kristal mod into .love and .exe for distribution. See example-workflow.yml.

Additionally, it applies any git patch files in `<your mod>/patches`. These patches should be non-critical to the mod's functionality (e.g. adjusting the MainMenu).

Each file in output.zip should be uploaded seperately, so users can choose which version to download.
