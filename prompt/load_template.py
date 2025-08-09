import os
from jinja2 import Environment, FileSystemLoader

def load_prompt_template(template_name: str, **kwargs):
    template_dir = os.path.join(os.path.dirname(__file__), "../resources/template/prompt")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(f"{template_name}.jinja-md")
    return template.render(**kwargs)



# print(load_prompt_template("code_sys", context="abc"))