from flask import Blueprint

blueprint = Blueprint(
    "resume_blueprint",
    __name__,
    url_prefix="/resume",
    template_folder="templates",
)
