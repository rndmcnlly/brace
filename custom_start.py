import os
import json
import logging
import shutil

os.environ["WEBUI_SECRET_KEY"] = "..."
from apps.webui.models.models import Models, ModelForm
from apps.webui.models.functions import Functions, FunctionForm

# Import functions

from config import FUNCTIONS_DIR
from apps.webui.utils import load_function_module_by_id

with open("functions.json") as f:
    functions_specifications = json.load(f)
    for spec in functions_specifications:
        src_function_path = os.path.join("/functions", f"{spec['id']}.py")
        with open(src_function_path, "r") as f:
            spec['content'] = f.read()
        form_data = FunctionForm(**spec)
        dst_function_path = os.path.join(FUNCTIONS_DIR, f"{form_data.id}.py")
        with open(dst_function_path, "w") as f:
            f.write(form_data.content)
        function_module, function_type, frontmatter = load_function_module_by_id(
            form_data.id
        )
        if function := Functions.get_function_by_id(form_data.id):
            print(f"Updating function: {form_data.id}")
            Functions.update_function_by_id(form_data.id, form_data)
        else:
            print(f"Inserting function: {form_data.id}")
            Functions.insert_new_function("custom-start", function_type, form_data)

# Import models

with open("models.json") as f:
    models_specifications = json.load(f)
    for spec in models_specifications:
        form_data = ModelForm(**spec["info"])
        if model := Models.get_model_by_id(form_data.id):
            print(f"Updating model: {form_data.id}")
            Models.update_model_by_id(form_data.id, form_data)
        else:
            print(f"Inserting model: {form_data.id}")
            Models.insert_new_model(form_data, "custom-start")