from django.dispatch import Signal

# Emitted when we detect all dependencies of a ProjectBuild being "FINISHED"
projectbuild_finished = Signal(providing_args=["projectbuild"])
