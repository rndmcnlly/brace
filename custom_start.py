import os
import json
import logging
import shutil
import base64
import mimetypes

os.environ["WEBUI_SECRET_KEY"] = "..."

from open_webui.apps.webui.models.models import Models, ModelForm
from open_webui.apps.webui.models.functions import Functions, FunctionForm
from open_webui.apps.webui.models.prompts import Prompts, PromptForm

from open_webui.config import FUNCTIONS_DIR
from open_webui.apps.webui.utils import load_function_module_by_id

with open("prompts.json") as f:
    prompt_specifications = json.load(f)
    for spec in prompt_specifications:
        form_data = PromptForm(**spec)
        if prompt := Prompts.get_prompt_by_command(form_data.command):
            print(f"Updating prompt: {form_data.command}")
            Prompts.update_prompt_by_command(form_data.command, form_data)
        else:
            print(f"Inserting prompt: {form_data.command}")
            Prompts.insert_new_prompt(spec["user_id"], form_data)
        
# Import functions

with open("functions.json") as f:
    functions_specifications = json.load(f)
    for spec in functions_specifications:
        src_function_path = os.path.join("/functions", f"{spec['id']}.py")
        with open(src_function_path, "r") as f:
            spec['content'] = f.read()
        form_data = FunctionForm(**spec)
        if function := Functions.get_function_by_id(form_data.id):
            print(f"Updating function: {form_data.id}")
            Functions.update_function_by_id(form_data.id, form_data)
        else:
            print(f"Inserting function: {form_data.id}")
            Functions.insert_new_function("custom-start", spec["type"], form_data)
        Functions.update_function_by_id(form_data.id, {
            "is_active": spec["is_active"],
            "is_global": spec["is_global"]
        })

# Import models

with open("models.json") as f:
    models_specifications = json.load(f)
    for spec in models_specifications:
        if spec["info"]["params"]["system"].startswith("@"):
            filename = spec["info"]["params"]["system"][1:]
            spec["info"]["params"]["system"] = open(filename, "r").read()
        if spec["info"]["meta"]["profile_image_url"].startswith("@"):
            filename = spec["info"]["meta"]["profile_image_url"][1:]
            mimetype, _ = mimetypes.guess_type(filename)
            data = open(filename, "rb").read()
            spec["info"]["meta"]["profile_image_url"] = f"data:{mimetype};base64,{base64.b64encode(data).decode('utf-8')}"
        form_data = ModelForm(**spec["info"])
        if model := Models.get_model_by_id(form_data.id):
            print(f"Updating model: {form_data.id}")
            Models.update_model_by_id(form_data.id, form_data)
        else:
            print(f"Inserting model: {form_data.id}")
            Models.insert_new_model(form_data, "custom-start")
